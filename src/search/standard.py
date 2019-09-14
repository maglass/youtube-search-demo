import json
import requests
from copy import copy
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

_SEARCH_API_HOST = 'http://13.125.252.81:9200'


@csrf_exempt
def search(request):
    params = request.GET
    query = params.get('q')
    start = params.get('s', 0)
    number = params.get('n', 10)
    versions = params.getlist('v')

    output = dict()
    meta = dict()
    ids = dict()
    for ver in versions:
        if ver in ['expansion-indices', 'ranking']:
            index_name = 'collection-final'
        else:
            index_name = 'collection-{}'.format(ver)

        contents = _search(index_name, ver, query, start, number)
        documents = _get_documents(contents)
        if ver in ['expansion-indices', 'ranking']:
            documents = _append_indices(documents, index_name, ['title_indices', 'desc_indices'])
        else:
            documents = _append_indices(documents, index_name, ['title'])

        output[ver] = documents
        meta[ver] = _get_meta(contents)
        ids[ver] = set(d['_id'] for d in documents)

    only_ver1 = ids[versions[0]] - ids[versions[1]]
    only_ver2 = ids[versions[1]] - ids[versions[0]]
    for ver, targets in zip(versions, [only_ver1, only_ver2]):
        new = list()
        for oo in output[ver]:
            doc = copy(oo)
            if doc['_id'] in targets:
                doc['only'] = True
                meta[ver]['only'] = meta[ver].get('only', 0) + 1
            else:
                doc['only'] = False
            new.append(doc)
        output[ver] = new

    response = dict()
    for ver in versions:
        response[ver] = dict()
        response[ver]['docs'] = output[ver]
        response[ver]['meta'] = meta[ver]
    return HttpResponse(json.dumps(response), content_type='application/json')


def _search(index_name, version, query, start, number):
    headers = {'Content-Type': 'application/json'}
    params = _get_params(version, query, start, number)

    data = json.dumps(params)
    rr = requests.get(_get_search_url(index_name), headers=headers, data=data)

    content = rr.json()
    return content


def _get_meta(contents):
    if 'hits' not in contents:
        return dict()

    total = contents['hits']['total']

    meta = dict()
    meta['total'] = total
    return meta


def _get_documents(contents):
    if 'hits' not in contents:
        return list()
    return contents['hits']['hits']


def _append_indices(documents, index_name, fields):
    output = list()
    for dd in documents:
        oo = copy(dd)
        oo['indices'] = _get_indices(dd['_id'], index_name, fields)
        output.append(oo)
    return output


def _get_indices(doc_id, index_name, fields):
    headers = {'Content-Type': 'application/json'}
    url = '{}/{}/_doc/{}/_termvectors'.format(_SEARCH_API_HOST, index_name, doc_id)

    body = {
        "fields": fields,
        "offsets": True,
        "payloads": True,
        "positions": True,
        "term_statistics": True,
        "field_statistics": True
    }
    rr = requests.get(url, headers=headers, data=json.dumps(body))
    content = rr.json()

    output = dict()
    for ff in fields:
        if ff not in content['term_vectors']:
            output[ff] = list()
        else:
            tokens = list((content['term_vectors'][ff].get('terms').keys()))

            if ff == 'title':
                output['title_indices'] = tokens
            else:

                output[ff] = tokens
    return output


def _get_search_url(index_name):
    return '{}/{}/_search'.format(_SEARCH_API_HOST, index_name)


def _get_params(version, query, start, number):
    if version in ['standard', 'nori-dict', 'nori']:
        return {
            "query": {
                'match': {
                    "title": {
                        "query": query,
                        "operator": "and"
                    }
                },
            },
            'from': start,
            'size': number
        }

    if version in ['expansion-indices']:
        return {
            "query": {
                "multi_match": {
                    "query": query,
                    "operator": "and",
                    "fields": ["title_indices", "desc_indices"]
                },
            },
            'from': start,
            'size': number
        }

    if version in ['ranking']:
        return {
            'from': start,
            'size': number,
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "operator": "and",
                            "fields": ["title_indices", "desc_indices"]
                        }},
                    "boost_mode": "replace",
                    "score_mode": "sum",
                    "functions": [
                        {
                            "filter": {
                                "match": {
                                    "title_indices": {"query": query, "operator": "and"}
                                }
                            },
                            "weight": 0.7
                        },
                        {
                            "filter": {
                                "match": {
                                    "desc_indices": {"query": query, "operator": "and"}
                                }
                            },
                            "weight": 0.3
                        },
                        {
                            "script_score": {
                                "script": {
                                    "source": "doc['caption_quality'].value"
                                }
                            },
                            "weight": 0.2
                        },
                        {
                            "script_score": {
                                "script": {
                                    "source": "doc['image_quality'].value"
                                }
                            },
                            "weight": 0.1
                        }
                    ]
                }
            }
        }

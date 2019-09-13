import json
import requests
from copy import copy
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

_SEARCH_API_HOST = 'http://13.125.252.81:9200'
_STANDARD_COLLECTION = 'collection-desc-tokens'


@csrf_exempt
def search(request):
    params = request.GET
    query = params.get('q')
    start = params.get('s', 0)
    number = params.get('n', 10)

    headers = {'Content-Type': 'application/json'}
    url = _get_search_api_url(_STANDARD_COLLECTION)

    body = {
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
    rr = requests.get(url, headers=headers, data=json.dumps(body))
    content = rr.json()

    documents = content['hits']['hits']

    docs = list()
    for dd in documents:
        temp = copy(dd)
        title_indices, desc_indices = term(dd['_id'])
        temp['terms'] = title_indices
        temp['desc_indices'] = desc_indices
        docs.append(temp)
    content['hits']['hits'] = docs
    return HttpResponse(json.dumps(content), content_type='application/json')


def term(doc_id):
    headers = {'Content-Type': 'application/json'}
    url = 'http://13.125.252.81:9200/{}/_doc/{}/_termvectors'.format(_STANDARD_COLLECTION, doc_id)

    body = {
        "fields": ["title_indices", 'desc_indices'],
        "offsets": True,
        "payloads": True,
        "positions": True,
        "term_statistics": True,
        "field_statistics": True
    }
    rr = requests.get(url, headers=headers, data=json.dumps(body))
    content = rr.json()

    return list(content['term_vectors']['title_indices']['terms'].keys()), list(
        content['term_vectors']['desc_indices']['terms'].keys())


def _get_search_api_url(collection_name):
    return '{}/{}/_search'.format(_SEARCH_API_HOST, collection_name)

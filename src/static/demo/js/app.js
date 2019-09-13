new Vue({
    el: '#app',
    delimiters: ['${', '}'],
    data: {
        query: '다이어트',
        start: 0,
        number: 5,
        meta1: {},
        meta2: {},
        documents: [],
        documents2: [],
        case_one_model: "standard",
        case_two_model: "ranking"
    },
    methods: {
        pressSearchBtn: function () {
            this._callSearchApi()
        },
        _callSearchApi: function () {
            let query = this.query;
            let start = this.start;
            let number = this.number;


            let url = '/search?q=' + query;
            url += '&s=' + start;
            url += '&n=' + number;
            url += '&v=' + this.case_one_model;
            url += '&v=' + this.case_two_model;

            let self = this;
            axios.get(url)
                .then(function (response) {
                    self.meta1 = response['data'][self.case_one_model]['meta'];
                    self.documents = [];
                    response['data'][self.case_one_model]['docs'].forEach(function (d) {
                            let _source = d['_source'];
                            _source['score'] = d['_score'];
                            _source['img_url'] = 'https://img.youtube.com/vi/' + _source['video_id'] + '/maxresdefault.jpg';
                            _source['url'] = 'https://www.youtube.com/watch?v=' + _source['video_id'];
                            _source['only'] = d['only'];
                            _source['title_indices'] = d['indices']['title_indices'];
                            _source['desc_indices'] = d['indices']['desc_indices'];

                            self.documents.push(_source);
                        }
                    );

                    self.meta2 = response['data'][self.case_two_model]['meta'];
                    self.documents2 = [];
                    response['data'][self.case_two_model]['docs'].forEach(function (d) {
                            let _source = d['_source'];
                            _source['score'] = d['_score'];
                            _source['img_url'] = 'https://img.youtube.com/vi/' + _source['video_id'] + '/maxresdefault.jpg';
                            _source['url'] = 'https://www.youtube.com/watch?v=' + _source['video_id'];
                            _source['only'] = d['only'];
                            _source['title_indices'] = d['indices']['title_indices'];
                            _source['desc_indices'] = d['indices']['desc_indices'];

                            self.documents2.push(_source);
                        }
                    )
                });
        },
    }
});

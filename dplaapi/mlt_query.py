"""
dplaapi.mlt_query
~~~~~~~~~~~~~~~~~

Elasticsearch "More Like This" query
"""

from .field_or_subfield import field_or_subfield


query_skel = {
    'query': {
        'more_like_this': {
            'fields': [
                'sourceResource.title', 'sourceResource.subject'
            ],
            'min_term_freq': 1,
            'min_doc_freq': 5,
            'max_query_terms': 25,
            'min_word_length': 3
            # TODO: add custom analyzer to the index _settings that removes
            # stopwords, etc., and use that analyzer here.
        }
    },
    'sort': [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}}
    ]
}


def like_clause_element(doc_id):
    """An element of a more_like_this "like" clause's array"""
    return {'_index': 'dpla_alias', '_type': 'item', '_id': doc_id}


class MLTQuery():
    """Elasticsearch "More Like This" API query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    Instance attributes:
    - query: The dict that will be serialized to JSON for the query.
    """
    def __init__(self, params: dict):
        """
        Arguments:
        - params: The request's querystring parameters
        """
        self.query = query_skel.copy()
        like_list = [like_clause_element(x) for x in params['ids']]
        self.query['query']['more_like_this']['like'] = like_list

        if 'fields' in params:
            self.query['_source'] = params['fields'].split(',')

        self.query['from'] = (params['page'] - 1) * params['page_size']
        self.query['size'] = params['page_size']

        if 'sort_by' in params:
            self.add_sort_clause(params)

    def add_sort_clause(self, params):
        actual_field = field_or_subfield[params['sort_by']]
        if actual_field == 'sourceResource.spatial.coordinates':
            pin = params['sort_by_pin']
            self.query['sort'] = [
                {
                    '_geo_distance': {
                        'sourceResource.spatial.coordinates': pin,
                        'order': 'asc',
                        'unit': 'mi'
                    }
                }
            ]
        else:
            self.query['sort'] = [
                {actual_field: {'order': params['sort_order']}},
                {'_score': {'order': 'desc'}}]

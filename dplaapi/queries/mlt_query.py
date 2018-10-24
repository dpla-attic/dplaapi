"""
dplaapi.mlt_query
~~~~~~~~~~~~~~~~~

Elasticsearch "More Like This" query
"""

from .base_query import BaseQuery


query_skel = {
    'query': {
        'more_like_this': {
            'fields': [
                'sourceResource.title.mlt', 'sourceResource.subject.mlt'
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


class MLTQuery(BaseQuery):
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

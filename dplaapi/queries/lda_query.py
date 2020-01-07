"""
dplaapi.lda_query
~~~~~~~~~~~~~~~~~

Cosine similarity search on LDA vector
"""

from .base_query import BaseQuery

query_skel = {
    'query': {
        'script_score': {
            'query': {
                'bool': {
                    'must': {
                        'match_all': {},
                    },
                    'must_not': {
                        'term': {
                            'id': ''
                        }
                    }
                }
            },
            'script': {
                'source':
                    'cosineSimilarity(params.queryVector, doc.ldaVector)',
                'params': {
                    'queryVector': []
                }
            }
        }
    },
    'sort': [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}}
    ]
}


class LDAQuery(BaseQuery):
    """Elasticsearch Cosine Similarity query on LDA vector

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

        vector_str = params['vector']
        vector = [float(s) for s in vector_str]
        self.query['query']['script_score']['script']['params']['queryVector']\
            = vector

        self.query['query']['script_score']['query']['bool']['must_not']['term']['id'] = params['id']

        if 'fields' in params:
            self.query['_source'] = params['fields'].split(',')

        self.query['from'] = (params['page'] - 1) * params['page_size']
        self.query['size'] = params['page_size']

        if 'sort_by' in params:
            self.add_sort_clause(params)

"""
dplaapi.necropolis_query
~~~~~~~~~~~~~~~~~~~~

Elasticsearch Search Necropolis query
"""

from .base_query import BaseQuery

query_skel_specific_id = {
    'sort': {'id': {'order': 'asc'}},
    'from': 0,
    'size': 1
}


class NecropolisQuery(BaseQuery):
    """Elasticsearch Search Necropolis query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    Instance attributes:
    - query: The dict that will be serialized to JSON for the query.
    """

    def __init__(self, params: dict):
        """Initialize the NecropolisQuery

        Arguments:
        - params: The request's querystring parameters
        """

        self.query = query_skel_specific_id.copy()
        self.query['query'] = {'terms': {'id': [params['id']]}}

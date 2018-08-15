"""
dplaapi.search_query
~~~~~~~~~~~~~~~~~~~~

Elasticsearch Search API query
"""

from . import types


skel = {
    'sort': {
        '_score': {
            'order': 'desc'
        },
        'id': {
            'order': 'asc'
        }
    },
    'from': 0,
    'size': 10
}


must_skel = {
    'query_string': {
        'default_operator': 'AND',
        'lenient': True
    }
}


# Fields available to query in a 'query_string' clause
fields_to_query = {
    'sourceResource.title': '2',
    'sourceResource.description': '0.75',
    'sourceResource.subject.name': '1',
    'sourceResource.collection.title': '1',
    'sourceResource.collection.description': '1',
    'sourceResource.contributor': '1',
    'sourceResource.creator': '1',
    'sourceResource.extent': '1',
    'sourceResource.format': '1',
    'sourceResource.language.name': '1',
    'sourceResource.publisher': '1',
    'sourceResource.relation': '1',
    'sourceResource.spatial.name': '1',
    'sourceResource.specType': '1',
    'sourceResource.subject.name': '1',
    'sourceResource.type': '1',
    'dataProvider': '1',
    'intermediateProvider': '1',
    'provider.name': '1'
}


class SearchQuery():
    """Elasticsearch Search API query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    - :attr:`query`
    """
    def __init__(self, params):
        """Initialize the SearchQuery

        :param dplaapi.types.ItemsQueryType params:
            The request's querystring parameters
        """
        assert isinstance(params, types.ItemsQueryType)
        self.query = skel.copy()
        if params.is_match_all():
            self.query['query'] = {'match_all': {}}
        else:
            self.query['query'] = {'bool': {'must': []}}
            if params.q:
                must = must_skel.copy()
                must['query_string']['query'] = params.q
                must['query_string']['fields'] = \
                    ['^'.join(item) for item in fields_to_query.items()]
                self.query['query']['bool']['must'].append(must)

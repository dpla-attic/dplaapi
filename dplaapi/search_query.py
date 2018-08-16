"""
dplaapi.search_query
~~~~~~~~~~~~~~~~~~~~

Elasticsearch Search API query
"""


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


# Fields available to query in a 'query_string' clause.
#
# The key is the field name and the value is the boost, and also indicates if
# the field will be used in a "simple search" "q=" query.
#
fields_to_query = {
    'dataProvider': '1',
    'hasView': None,
    'hasView.@id': None,
    'hasView.format': None,
    'hasView.rights': None,
    'id': None,
    'intermediateProvider': '1',
    'isShownAt': None,
    'object': None,
    'provider': None,
    'provider.@id': None,
    'provider.name': '1',
    'rights': None,
    'sourceResource.collection': None,
    'sourceResource.collection.@id': None,
    'sourceResource.collection.description': '1',
    'sourceResource.collection.id': None,
    'sourceResource.collection.title': '1',
    'sourceResource.contributor': '1',
    'sourceResource.creator': '1',
    'sourceResource.description': '0.75',
    'sourceResource.extent': '1',
    'sourceResource.format': '1',
    'sourceResource.identifier': None,
    'sourceResource.language': None,
    'sourceResource.language.iso639_3': None,
    'sourceResource.language.name': '1',
    'sourceResource.publisher': '1',
    'sourceResource.relation': '1',
    'sourceResource.rights': None,
    'sourceResource.spatial.coordinates': None,
    'sourceResource.spatial.country': '0.75',
    'sourceResource.spatial.county': '1',
    'sourceResource.spatial.name': '1',
    'sourceResource.spatial.region': '1',
    'sourceResource.spatial.state': '0.75',
    'sourceResource.specType': '1',
    'sourceResource.subject': None,
    'sourceResource.subject.name': '1',
    'sourceResource.title': '2',
    'sourceResource.type': '1'
}


def q_fields_clause_items(d: dict):
    """Generator over items for a 'query_string' fields clause"""
    for item in d.items():
        if item[1]:
            yield '^'.join(item)


def q_fields_clause(d: dict):
    """Return an array for the 'fields' clause of a "simple search" query"""
    return [val for val in q_fields_clause_items(d)]


def single_field_fields_clause(field, boost):
    if boost:
        return ['^'.join([field, boost])]
    else:
        return [field]


class SearchQuery():
    """Elasticsearch Search API query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    - :attr:`query`
    """
    def __init__(self, params: dict):
        """Initialize the SearchQuery

        :param dplaapi.types.ItemsQueryType params:
            The request's querystring parameters
        """
        self.query = skel.copy()
        if not params.keys():
            self.query['query'] = {'match_all': {}}
        else:
            self.query['query'] = {'bool': {'must': []}}
            for field, term in params.items():
                must = must_skel.copy()
                must['query_string']['query'] = term
                if field == 'q':
                    must['query_string']['fields'] = \
                        q_fields_clause(fields_to_query)
                else:
                    boost = fields_to_query[field]
                    must['query_string']['fields'] = \
                        single_field_fields_clause(field, boost)
                self.query['query']['bool']['must'].append(must)

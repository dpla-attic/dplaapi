"""
dplaapi.search_query
~~~~~~~~~~~~~~~~~~~~

Elasticsearch Search API query
"""


skel = {
    'sort': [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}}
    ],
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


sort_by = {
    '@id': '@id',
    'hasView.@id': 'hasView.@id',
    'hasView.format': 'hasView.format',
    'id': 'id',
    'isPartOf.@id': 'isPartOf.@id',
    'isPartOf.name': 'isPartOf.name.not_analyzed',
    'isShownAt': 'isShownAt',
    'object': 'object',
    'provider.@id': 'provider.@id',
    'provider.name': 'provider.name.not_analyzed',
    'sourceResource.contributor': 'sourceResource.contributor',
    'sourceResource.date.begin': 'sourceResource.date.begin.not_analyzed',
    'sourceResource.date.end': 'sourceResource.date.end.not_analyzed',
    'sourceResource.extent': 'sourceResource.extent',
    'sourceResource.format': 'sourceResource.format',
    'sourceResource.language.iso639_3': 'sourceResource.language.iso639_3',
    'sourceResource.language.name': 'sourceResource.language.name',
    'sourceResource.spatial.city': 'sourceResource.spatial.city.not_analyzed',
    'sourceResource.spatial.coordinates': 'sourceResource.spatial.coordinates',
    'sourceResource.spatial.country': 'sourceResource.spatial.country'
                                      '.not_analyzed',
    'sourceResource.spatial.county': 'sourceResource.spatial.county'
                                     '.not_analyzed',
    'sourceResource.spatial.name': 'sourceResource.spatial.name.not_analyzed',
    'sourceResource.spatial.region': 'sourceResource.spatial.region'
                                     '.not_analyzed',
    'sourceResource.spatial.state': 'sourceResource.spatial.state'
                                    '.not_analyzed',
    'sourceResource.subject.@id': 'sourceResource.subject.@id',
    'sourceResource.subject.name': 'sourceResource.subject.name.not_analyzed',
    'sourceResource.temporal.begin': 'sourceResource.temporal.begin'
                                     '.not_analyzed',
    'sourceResource.temporal.end': 'sourceResource.temporal.end.not_analyzed',
    'sourceResource.title': 'sourceResource.title.not_analyzed',
    'sourceResource.type': 'sourceResource.type'
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


def fields_and_constraints(params):
    """Given querystring parameters, return a tuple of dicts for those that are
    record fields and those that are query constraints"""
    fields = {k: v for (k, v) in params.items()
              if k in fields_to_query or k == 'q'}
    constraints = {k: v for (k, v) in params.items()
                   if k not in fields_to_query and k != 'q'}
    return (fields, constraints)


class SearchQuery():
    """Elasticsearch Search API query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    Instance attributes:
    - query: The dict that will be serialized to JSON for the query.
    """
    def __init__(self, params: dict):
        """Initialize the SearchQuery

        Arguments:
        - params: The request's querystring parameters
        """
        self.query = skel.copy()
        fields, constraints = fields_and_constraints(params)
        if not fields.keys():
            self.query['query'] = {'match_all': {}}
        else:
            self.query['query'] = {'bool': {'must': []}}
            for field, term in fields.items():
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

        if 'fields' in constraints:
            self.query['_source'] = constraints['fields'].split(',')

        self.query['from'] = \
            (constraints['page'] - 1) * constraints['page_size']
        self.query['size'] = constraints['page_size']

        if 'sort_by' in constraints:
            actual_field = sort_by[constraints['sort_by']]
            if actual_field == 'sourceResource.spatial.coordinates':
                pin = constraints['sort_by_pin']
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
                    {actual_field: {'order': constraints['sort_order']}},
                    {'_score': {'order': 'desc'}}]

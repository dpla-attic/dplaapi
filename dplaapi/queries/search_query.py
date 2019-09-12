"""
dplaapi.search_query
~~~~~~~~~~~~~~~~~~~~

Elasticsearch Search API query
"""

import re
from apistar.exceptions import ValidationError
from dplaapi.facets import facets
from dplaapi.field_or_subfield import field_or_subfield
from .base_query import BaseQuery

query_skel_search = {
    'sort': [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}}
    ],
    'track_total_hits': 'true'
}

query_skel_specific_ids = {
    'sort': {'id': {'order': 'asc'}},
    'from': 0,
    'size': 50
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
    'admin.contributingInstitution': None,
    'sourceResource.collection': None,
    'sourceResource.collection.@id': None,
    'sourceResource.collection.description': '1',
    'sourceResource.collection.id': None,
    'sourceResource.collection.title': '1',
    'sourceResource.contributor': '1',
    'sourceResource.creator': '1',
    'sourceResource.date.begin': None,
    'sourceResource.date.end': None,
    'sourceResource.description': '0.75',
    'sourceResource.extent': '1',
    'sourceResource.format': '1',
    'sourceResource.identifier': None,
    'sourceResource.language': None,
    'sourceResource.language.iso639_3': None,
    'sourceResource.language.name': '1',
    'sourceResource.publisher': '1',
    'sourceResource.relation': '1',
    'sourceResource.rights': '1',
    'sourceResource.spatial': None,
    'sourceResource.spatial.coordinates': None,
    'sourceResource.spatial.country': '0.75',
    'sourceResource.spatial.county': '1',
    'sourceResource.spatial.name': '1',
    'sourceResource.spatial.region': '1',
    'sourceResource.spatial.state': '0.75',
    'sourceResource.specType': '1',
    'sourceResource.subject': None,
    'sourceResource.subject.name': '1',
    'sourceResource.temporal.begin': None,
    'sourceResource.temporal.end': None,
    'sourceResource.title': '2',
    'sourceResource.type': '1'
}

# We let the user query on some fields that are objects. We really mean
# "field.*" ... or else Elasticsearch won't query its subfields.
object_wildcards = {
    'sourceResource.spatial': 'sourceResource.spatial.*',
    'provider': 'provider.*'
}

temporal_search_field_pat = re.compile(r'(?P<field>.*)?\.(?P<modifier>.*)$')


def q_fields_clause_items(d: dict):
    """Generator over items for a 'query_string' fields clause"""
    for item in d.items():
        if item[1]:
            yield '^'.join(item)


def q_fields_clause(d: dict):
    """Return an array for the 'fields' clause of a "simple search" query"""
    return [val for val in q_fields_clause_items(d)]


def single_field_fields_clause(field, boost, constraints):
    """The 'fields' part for one 'query_string' clause"""
    if constraints.get('exact_field_match') == 'true':
        field_to_use = field_or_subfield.get(field, field)
    else:
        field_to_use = object_wildcards.get(field, field)
    if boost:
        return ['^'.join([field_to_use, boost])]
    else:
        return [field_to_use]


def is_field_related(param_name):
    return param_name in fields_to_query or param_name == 'q' \
           or param_name == 'ids' or param_name.endswith('.before') \
           or param_name.endswith('.after')


def fields_and_constraints(params):
    """Given querystring parameters, return a tuple of dicts for those that are
    record fields and those that are query constraints"""
    fields = {k: v for (k, v) in params.items() if is_field_related(k)}
    constraints = {k: v for (k, v) in params.items()
                   if not is_field_related(k)}
    return (fields, constraints)


def clean_facet_name(name):
    """Clean facet name, without geo distance ":" suffix"""
    return name.partition(':')[0]


def facets_for(field_name, size):
    """Return a dict for the aggregation (facet) for the given field

    Arguments:
    - size: Number of buckets per aggregation, where applicable.  Ignored for
            geo_distance and date facets.
    """

    if field_name.startswith('sourceResource.spatial.coordinates'):
        parts = field_name.partition(':')
        field, coords_part = parts[0], parts[2]
        origin = coords_part.replace(':', ',')
        ranges = \
            [{'from': i, 'to': i + 99} for i in range(0, 2100, 100)] \
            + [{'from': 2100}]
        return {
            'geo_distance': {
                'field': field,
                'origin': origin,
                'unit': 'mi',
                'ranges': ranges
            }
        }

    else:
        try:
            actual_field, facet_type = facets[field_name]
        except KeyError:
            raise ValidationError("%s is not a facetable field" % field_name)
        if facet_type == 'date_histogram':
            interval = date_facet_interval(field_name)
            if interval in ['month', 'year']:
                return date_histogram_agg(field_name,
                                          actual_field,
                                          interval,
                                          size)
        else:
            return {'terms': {'field': actual_field, 'size': size}}


def date_histogram_agg(facet_name, actual_field, interval, size):
    # The minimum date in the filter 'range' below keeps us from getting
    # HTTP 503 errors from Elasticsearch due to using too many aggregation
    # buckets (more than 5000).
    min_date_filter = {
        'month': 'now-416y',
        'year': 'now-2000y'
    }
    key_format = {
        'month': 'yyyy-MM',
        'year': 'yyyy'
    }
    return {
        'filter': {
            'range': {
                actual_field: {
                    'gte': min_date_filter[interval],
                    'lte': 'now'
                }
            }
        },
        'aggs': {
            facet_name: {
                'date_histogram': {
                    'field': actual_field,
                    'interval': interval,
                    'format': key_format[interval],
                    'min_doc_count': 1,
                    'order': {'_key': 'desc'}
                }
            }
        }
    }


def date_facet_interval(facet_name):
    """Return the date histogram interval for the given facet name

    The default is "year".
    """
    parts = facet_name.rpartition('.')
    interval = parts[2]
    if interval in ['month', 'year', 'decade', 'century']:
        return interval
    else:
        return 'year'


def facets_clause(facets_string, size):
    """Return a dict for the whole Elasticsearch 'aggs' property"""
    names = facets_string.split(',')
    return {clean_facet_name(name): facets_for(name, size) for name in names}


def facet_size(constraints):
    size = int(constraints.get('facet_size', 50))
    # The old API app truncated the size like this, and we do so here for
    # consistency.
    if size > 2000:
        size = 2000
    return size


class SearchQuery(BaseQuery):
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
        fields, constraints = fields_and_constraints(params)

        if 'op' in params and params['op'] == 'OR':
            self.bool_type = 'should'
        else:
            self.bool_type = 'must'

        if not fields.keys():
            self.query = query_skel_search.copy()
            self.query['query'] = {'match_all': {}}

        elif 'ids' in fields:
            self.query = query_skel_specific_ids.copy()
            self.query['query'] = {'terms': {'id': fields['ids']}}

        else:
            self.query = query_skel_search.copy()
            self.query['query'] = {'bool': {self.bool_type: []}}
            for field, term in fields.items():
                if field.endswith('.before') or field.endswith('.after'):
                    self.add_range_clause(field, term)
                else:
                    self.add_query_string_clause(field, term, constraints)

        if 'fields' in constraints:
            self.query['_source'] = constraints['fields'].split(',')

        if 'from' not in self.query:
            self.query['from'] = \
                (constraints['page'] - 1) * constraints['page_size']
            self.query['size'] = constraints['page_size']

        if 'sort_by' in constraints:
            self.add_sort_clause(constraints)

        if 'facets' in constraints:
            size = facet_size(constraints)
            self.query['aggs'] = facets_clause(constraints['facets'], size)

        if 'random' in constraints:
            # Override all other query parameters and return one random record
            self.query["query"] = {
                "function_score": {
                    "random_score": {}
                }
            }
            self.query["size"] = 1

    def add_query_string_clause(self, field, term, constraints):
        clause = {
            'query_string': {
                'query': term,
                'default_operator': 'AND',
                'lenient': True
            }
        }

        if field == 'q':
            clause['query_string']['fields'] = \
                q_fields_clause(fields_to_query)
        elif field == 'random':
            pass  # do nothing
        else:
            boost = fields_to_query[field]
            clause['query_string']['fields'] = \
                single_field_fields_clause(field, boost, constraints)

        self.query['query']['bool'][self.bool_type].append(clause)

    def add_range_clause(self, field_w_mod, term):
        match_obj = temporal_search_field_pat.match(field_w_mod)
        field = match_obj.group('field')
        modifier = match_obj.group('modifier')
        if modifier == 'before':
            key = "%s.begin" % field
            clause = {
                'range': {
                    key: {'lte': term}
                }
            }
        else:
            key = "%s.end" % field
            clause = {
                'range': {
                    key: {'gte': term}
                }
            }
        self.query['query']['bool'][self.bool_type].append(clause)

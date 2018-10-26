"""Test dplaapi.mlt_query"""

from dplaapi.queries.mlt_query import MLTQuery
from dplaapi.types import MLTQueryType


def test_MLTQuery_produces_query_with_like_clause():
    """MLTQuery pruduces a query with a "like" clause that has elements for
    all of the given item IDs"""
    params = MLTQueryType()
    params.update({'ids': ['id1', 'id2']})
    q = MLTQuery(params)
    assert q.query['query']['more_like_this']['like'] == [
        {'_type': 'item', '_id': 'id1'},
        {'_type': 'item', '_id': 'id2'}
    ]


def test_MLTQuery_has_correct_default_sort():
    """The search query without a sort requested has the correct 'sort'"""
    params = MLTQueryType()
    params.update({'ids': ['id1']})
    q = MLTQuery(params)
    assert q.query['sort'] == [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}},
    ]


def test_MLTQuery_has_sort_given_sort_by_param():
    """The search query has the correct sort if we got a sort_by parameter"""
    params = MLTQueryType({'sort_by': 'provider.name'})
    params.update({'ids': ['id1']})
    q = MLTQuery(params)
    assert q.query['sort'] == [
        {'provider.name.not_analyzed': {'order': 'asc'}},
        {'_score': {'order': 'desc'}}
    ]


def test_MLTQuery_does_geo_distance_sort():
    """A _geo_distance sort is performed for coordinates and pin params"""
    params = MLTQueryType({
        'sort_by': 'sourceResource.spatial.coordinates',
        'sort_by_pin': '26.15952,-97.99084'
    })
    params.update({'ids': ['id1']})
    q = MLTQuery(params)
    assert q.query['sort'] == [
        {
            '_geo_distance': {
                'sourceResource.spatial.coordinates': '26.15952,-97.99084',
                'order': 'asc',
                'unit': 'mi'
            }
        }
    ]


def test_MLTQuery_has_source_clause_for_fields_parameter():
    """If there's a "fields" query param, there's a "_source" property in the
    Elasticsearch query."""
    params = MLTQueryType({'fields': 'id'})
    params.update({'ids': ['id1']})
    q = MLTQuery(params)
    assert q.query['_source'] == ['id']

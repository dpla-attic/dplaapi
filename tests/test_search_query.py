"""Test dplaapi.search_query"""

import pytest
from dplaapi import search_query, types


def test_search_query_only_works_with_items_type():
    """SearchQuery can only be instantiated with an ItemsQueryType argument"""
    # ... For now. This will change if we implement collections queries.
    good_params = types.ItemsQueryType(q='test')
    bad_params = object()
    search_query.SearchQuery(good_params)  # no AssertionError here
    with pytest.raises(AssertionError):
        search_query.SearchQuery(bad_params)


def test_search_query_produces_match_all_for_no_query_terms():
    """SearchQuery produces 'match_all' syntax if there are no search terms"""
    params = types.ItemsQueryType()
    sq = search_query.SearchQuery(params)
    assert 'match_all' in sq.query['query']


def test_search_query_produces_bool_query_for_query_terms():
    """SearchQuery produces 'bool' syntax if there are search terms"""
    params = types.ItemsQueryType(q='test')
    sq = search_query.SearchQuery(params)
    assert 'bool' in sq.query['query']


def test_query_string_clause_has_all_correct_fields_for_q_query():
    """A 'q=' query hits all of the correct fields w field boosts"""
    params = types.ItemsQueryType(q='test')
    sq = search_query.SearchQuery(params)
    good_fields = [
        'sourceResource.title^2',
        'sourceResource.description^0.75',
        'sourceResource.subject.name^1',
        'sourceResource.collection.title^1',
        'sourceResource.collection.description^1',
        'sourceResource.contributor^1',
        'sourceResource.creator^1',
        'sourceResource.extent^1',
        'sourceResource.format^1',
        'sourceResource.language.name^1',
        'sourceResource.publisher^1',
        'sourceResource.relation^1',
        'sourceResource.spatial.name^1',
        'sourceResource.specType^1',
        'sourceResource.subject.name^1',
        'sourceResource.type^1',
        'dataProvider^1',
        'intermediateProvider^1',
        'provider.name^1',
    ]
    got_fields = sq.query['query']['bool']['must'][0]['query_string']['fields']
    assert got_fields.sort() == good_fields.sort()

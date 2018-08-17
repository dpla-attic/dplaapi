"""Test dplaapi.search_query"""

import re
from types import GeneratorType
from dplaapi import search_query, types


def test_search_query_produces_match_all_for_no_query_terms():
    """SearchQuery produces 'match_all' syntax if there are no search terms"""
    params = types.ItemsQueryType()
    sq = search_query.SearchQuery(params)
    assert 'match_all' in sq.query['query']
    assert 'bool' not in sq.query['query']


def test_search_query_produces_bool_query_for_query_terms():
    """SearchQuery produces 'bool' syntax if there are search terms"""
    params = types.ItemsQueryType({'q': 'test'})
    sq = search_query.SearchQuery(params)
    assert 'bool' in sq.query['query']
    assert 'match_all' not in sq.query['query']


def test_query_string_clause_has_all_correct_fields_for_q_query():
    """A 'q=' query hits all of the correct fields w field boosts"""
    params = types.ItemsQueryType({'q': 'test'})
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


def test_search_query_has_source_clause_for_fields_constraint():
    """If there's a "fields" query param, there's a "_source" property in the
    Elasticsearch query."""
    params = types.ItemsQueryType({'fields': 'id'})
    sq = search_query.SearchQuery(params)
    assert '_source' in sq.query


def test_search_query_can_handle_match_all_and_fields():
    """A correct ES query is generated for a match_all() with a _source prop"""
    params = types.ItemsQueryType({'fields': 'id'})
    sq = search_query.SearchQuery(params)
    assert 'match_all' in sq.query['query']
    assert '_source' in sq.query


def test_search_query_can_handle_bool_and_fields():
    """A correct ES query is generated for a bool with a _source prop"""
    params = types.ItemsQueryType({'provider.name': 'test', 'fields': 'id'})
    sq = search_query.SearchQuery(params)
    assert 'bool' in sq.query['query']
    assert '_source' in sq.query


def test_q_fields_clause_items_returns_correct_generator():
    thedict = {'a': '1', 'b': None, 'c': '2'}
    generator = search_query.q_fields_clause_items(thedict)
    assert isinstance(generator, GeneratorType)
    for item in generator:
        assert re.match(r'\w\^\d', item)


def test_q_fields_clause_returns_array():
    thedict = {'a': '1', 'b': None, 'c': '2'}
    assert search_query.q_fields_clause(thedict) == ['a^1', 'c^2']


def test_single_field_fields_clause_with_boost():
    assert search_query.single_field_fields_clause('field', '1') == ['field^1']


def test_single_field_fields_clause_no_boost():
    assert search_query.single_field_fields_clause('field', None) == ['field']


def test_fields_and_constraints_separates_parameters():
    """Given a dict of record field names and query constraints, it produces
    two dicts, one with the field names, and the other with the constraints.
    """
    params = {
        'dataProvider': 'x',
        'sourceResource.type': 'x',
        'fields': 'sourceResource.title'
    }
    ok = (
        {'dataProvider': 'x', 'sourceResource.type': 'x'},
        {'fields': 'sourceResource.title'}
    )
    assert search_query.fields_and_constraints(params) == ok

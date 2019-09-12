"""Test dplaapi.search_query"""

import re
import pytest
from types import GeneratorType
from apistar.exceptions import ValidationError
from dplaapi import types
from dplaapi.queries import search_query


def test_SearchQuery_produces_match_all_for_no_query_terms():
    """SearchQuery produces 'match_all' syntax if there are no search terms"""
    params = types.ItemsQueryType()
    sq = search_query.SearchQuery(params)
    assert 'match_all' in sq.query['query']
    assert 'bool' not in sq.query['query']


def test_SearchQuery_produces_bool_query_for_query_terms():
    """SearchQuery produces 'bool' syntax if there are search terms"""
    params = types.ItemsQueryType({'q': 'test'})
    sq = search_query.SearchQuery(params)
    assert 'bool' in sq.query['query']
    assert 'match_all' not in sq.query['query']


def test_SearchQuery_produces_terms_query_with_ids():
    """If given an 'ids' parameter, SearchQuery produces a 'terms' query with
    a list of the IDs"""
    params = {
        'ids': [
            '13283cd2bd45ef385aae962b144c7e6a',
            '00000062461c867a39cac531e13a48c1'
        ]
    }
    sq = search_query.SearchQuery(params)
    assert sq.query['query']['terms'] == {
        'id': [
            '13283cd2bd45ef385aae962b144c7e6a',
            '00000062461c867a39cac531e13a48c1'
        ]
    }


def test_query_string_clause_has_all_correct_fields_for_q_query():
    """A 'q=' query hits all of the correct fields w field boosts"""
    params = types.ItemsQueryType({'q': 'test'})
    sq = search_query.SearchQuery(params)
    good_fields = [
        'sourceResource.title^2',
        'sourceResource.description^0.75',
        'sourceResource.collection.title^1',
        'sourceResource.collection.description^1',
        'sourceResource.contributor^1',
        'sourceResource.creator^1',
        'sourceResource.extent^1',
        'sourceResource.format^1',
        'sourceResource.language.name^1',
        'sourceResource.publisher^1',
        'sourceResource.relation^1',
        'sourceResource.rights^1',
        'sourceResource.spatial.country^0.75',
        'sourceResource.spatial.county^1',
        'sourceResource.spatial.name^1',
        'sourceResource.spatial.region^1',
        'sourceResource.spatial.state^0.75',
        'sourceResource.specType^1',
        'sourceResource.subject.name^1',
        'sourceResource.type^1',
        'dataProvider^1',
        'intermediateProvider^1',
        'provider.name^1',
    ]
    got_fields = sq.query['query']['bool']['must'][0]['query_string']['fields']
    assert sorted(got_fields) == sorted(good_fields)


def test_SearchQuery_has_source_clause_for_fields_constraint():
    """If there's a "fields" query param, there's a "_source" property in the
    Elasticsearch query."""
    params = types.ItemsQueryType({'fields': 'id'})
    sq = search_query.SearchQuery(params)
    assert '_source' in sq.query


def test_SearchQuery_can_handle_match_all_and_fields():
    """A correct ES query is generated for a match_all() with a _source prop"""
    params = types.ItemsQueryType({'fields': 'id'})
    sq = search_query.SearchQuery(params)
    assert 'match_all' in sq.query['query']
    assert '_source' in sq.query


def test_SearchQuery_can_handle_bool_and_fields():
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
    result = search_query.single_field_fields_clause('field', '1', {})
    assert result == ['field^1']


def test_single_field_fields_clause_no_boost():
    result = search_query.single_field_fields_clause('field', None, {})
    assert result == ['field']


def test_single_field_fields_clause_subfield_exact_field_match():
    """single_field_fields_clause() uses the 'not_analyzed' subfield if
    'exact_field_match' is in effect."""
    constraints = {'exact_field_match': 'true'}
    result = search_query.single_field_fields_clause('dataProvider', None,
                                                     constraints)
    assert result == ['dataProvider.not_analyzed']


def test_single_field_fields_clause_object_wildcards():
    """single_field_fields_clause() picks up the ".*" for a field that's an
    object"""
    result = search_query.single_field_fields_clause(
        'sourceResource.spatial', None, {})
    assert result == ['sourceResource.spatial.*']


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


def test_SearchQuery_has_size_and_from():
    """The JSON generated by SearchQuery has 'size' and 'from' properties."""
    params = types.ItemsQueryType()
    sq = search_query.SearchQuery(params)
    assert 'size' in sq.query
    assert 'from' in sq.query


def test_SearchQuery_from_is_calculated_from_page_and_page_size():
    """The 'from' value in SearchQuery's JSON is calculated properly"""
    params = types.ItemsQueryType()
    sq1 = search_query.SearchQuery(params)
    assert sq1.query['from'] == 0
    params = types.ItemsQueryType({'page': '2', 'page_size': '2'})
    sq2 = search_query.SearchQuery(params)
    assert sq2.query['from'] == 2


def test_SearchQuery_has_correct_default_sort():
    """The search query without sort requested has the correct 'sort'"""
    params = types.ItemsQueryType()
    sq = search_query.SearchQuery(params)
    assert sq.query['sort'] == [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}},
    ]


def test_SearchQuery_has_sort_given_sort_by_param():
    """The search query has the correct sort if we got a sort_by parameter"""
    params = types.ItemsQueryType({'sort_by': 'sourceResource.type'})
    sq = search_query.SearchQuery(params)
    assert sq.query['sort'] == [
        {'sourceResource.type': {'order': 'asc'}},
        {'_score': {'order': 'desc'}}
    ]


def test_SearchQuery_uses_not_analyzed_field_where_necessary():
    """The search query specifies the not_analyzed (keyword) field if the
    requested fields needs it; usually when it's a text field."""
    params = types.ItemsQueryType({'sort_by': 'sourceResource.title'})
    sq = search_query.SearchQuery(params)
    assert sq.query['sort'] == [
        {'sourceResource.title.not_analyzed': {'order': 'asc'}},
        {'_score': {'order': 'desc'}}
    ]


def test_SearchQuery_does_geo_distance_sort():
    """A _geo_distance sort is performed for coordinates and pin params"""
    params = types.ItemsQueryType({
        'sort_by': 'sourceResource.spatial.coordinates',
        'sort_by_pin': '26.15952,-97.99084'
    })
    sq = search_query.SearchQuery(params)
    assert sq.query['sort'] == [
        {
            '_geo_distance': {
                'sourceResource.spatial.coordinates': '26.15952,-97.99084',
                'order': 'asc',
                'unit': 'mi'
            }
        }
    ]


def test_SearchQuery_add_range_clause_before():
    params = types.ItemsQueryType({'sourceResource.date.before': '2000'})
    sq = search_query.SearchQuery(params)
    assert sq.query['query']['bool']['must'][0] == {
        'range': {
            'sourceResource.date.begin': {'lte': '2000'}
        }
    }


def test_SearchQuery_add_range_clause_after():
    params = types.ItemsQueryType({'sourceResource.date.after': '2000'})
    sq = search_query.SearchQuery(params)
    assert sq.query['query']['bool']['must'][0] == {
        'range': {
            'sourceResource.date.end': {'gte': '2000'}
        }
    }


def test_clean_facet_name_works():
    """Facet names are cleaned for use as 'aggs' object keys"""
    assert search_query.clean_facet_name('x:y:z') == 'x'


def test_SearchQuery_adds_facets_to_query():
    """SearchQuery adds a 'facets' property to the query if a 'facets' param
    is given."""
    params = types.ItemsQueryType({'facets': 'provider.name'})
    sq = search_query.SearchQuery(params)
    assert 'aggs' in sq.query


def test_facets_clause_return_correct_dict(monkeypatch):
    """The dict comprehension for the facets clause works and it makes the
    right function calls"""
    def mock_facets_for(name, size):
        del(size)
        assert name in ['x', 'y']
        return {}
    monkeypatch.setattr(search_query, 'facets_for', mock_facets_for)
    assert search_query.facets_clause('x,y', 50) == {'x': {}, 'y': {}}


def test_facets_for_handles_keyword_field():
    """It makes a simple 'terms' clause"""
    assert search_query.facets_for('hasView.@id', 50) == {
        'terms': {'field': 'hasView.@id', 'size': 50}
    }


def test_facets_for_handles_text_field():
    """It uses the .not_analyzed field"""
    assert search_query.facets_for('intermediateProvider', 50) == {
        'terms': {'field': 'intermediateProvider.not_analyzed', 'size': 50}
    }


def test_facets_for_handles_date_field():
    assert search_query.facets_for('sourceResource.date.begin', 50) == {
        'filter': {
            'range': {
                'sourceResource.date.begin': {
                    'gte': 'now-2000y',
                    'lte': 'now'
                }
            }
        },
        'aggs': {
            'sourceResource.date.begin': {
                'date_histogram': {
                    'field': 'sourceResource.date.begin',
                    'interval': 'year',
                    'format': 'yyyy',
                    'min_doc_count': 1,
                    'order': {'_key': 'desc'}
                }
            }
        }
    }


def test_facets_for_histogram_for_month_or_year(mocker):
    """A date histogram aggregation is produced for month or year modifier"""
    mocker.patch('dplaapi.queries.search_query.date_histogram_agg')
    field = 'sourceResource.date.begin'
    for interval in ['month', 'year']:
        facet = "%s.%s" % (field, interval)
        search_query.facets_for(facet, 50)
        search_query.date_histogram_agg.assert_called_once_with(
            facet, field, interval, 50)
        search_query.date_histogram_agg.reset_mock()
    # Also for no modifier, which should default to "year" ...
    search_query.facets_for(field, 50)
    search_query.date_histogram_agg.assert_called_once_with(
        field, field, 'year', 50)


def test_SearchQuery_facets_for_handles_coordinates_field():
    f = 'sourceResource.spatial.coordinates:40.941258:-73.864468'
    ranges = [
        {'from': 0, 'to': 99}, {'from': 100, 'to': 199},
        {'from': 200, 'to': 299}, {'from': 300, 'to': 399},
        {'from': 400, 'to': 499}, {'from': 500, 'to': 599},
        {'from': 600, 'to': 699}, {'from': 700, 'to': 799},
        {'from': 800, 'to': 899}, {'from': 900, 'to': 999},
        {'from': 1000, 'to': 1099}, {'from': 1100, 'to': 1199},
        {'from': 1200, 'to': 1299}, {'from': 1300, 'to': 1399},
        {'from': 1400, 'to': 1499}, {'from': 1500, 'to': 1599},
        {'from': 1600, 'to': 1699}, {'from': 1700, 'to': 1799},
        {'from': 1800, 'to': 1899}, {'from': 1900, 'to': 1999},
        {'from': 2000, 'to': 2099}, {'from': 2100}]
    facets_clause = search_query.facets_for(f, 50)
    assert facets_clause == {
        'geo_distance': {
            'field': 'sourceResource.spatial.coordinates',
            'origin': '40.941258,-73.864468',
            'unit': 'mi',
            'ranges': ranges
        }
    }


def test_facets_for_raises_exception_for_bad_field_name():
    with pytest.raises(ValidationError):
        search_query.facets_for('x', 50)


def test_date_facet_interval_w_no_modifier():
    """With no modifier, it returns 'year'"""
    arg = 'sourceResource.date.begin'
    result = search_query.date_facet_interval(arg)
    assert result == 'year'


def test_date_facet_interval_w_year_modifier():
    """With '.year' modifier, it returns 'year'"""
    arg = 'sourceResource.date.begin.year'
    result = search_query.date_facet_interval(arg)
    assert result == 'year'


def test_date_facet_interval_w_month_modifier():
    arg = "sourceResource.date.begin.month"
    result = search_query.date_facet_interval(arg)
    assert result == 'month'


def test_date_histogram_agg_for_month():
    """With 'month', it produces the correct filter & date_histogram"""
    facet = 'sourceResource.date.begin.month'
    actual_field = 'sourceResource.date.begin'
    interval = 'month'
    result = search_query.date_histogram_agg(facet, actual_field, interval, 50)
    assert result == {
        'filter': {
            'range': {
                'sourceResource.date.begin': {
                    'gte': 'now-416y',
                    'lte': 'now'
                }
            }
        },
        'aggs': {
            'sourceResource.date.begin.month': {
                'date_histogram': {
                    'field': 'sourceResource.date.begin',
                    'interval': 'month',
                    'format': 'yyyy-MM',
                    'min_doc_count': 1,
                    'order': {'_key': 'desc'}
                }
            }
        }
    }


def test_facet_size_default():
    """facet_size() has default return value 50"""
    assert search_query.facet_size({}) == 50


def test_facet_size_returns_ok_facet_size_value():
    assert search_query.facet_size({'facet_size': '10'}) == 10


def test_face_size_truncates_facet_size_if_too_large():
    """It truncates values over 2000 to 2000.

    This is not ideal, but it is how the old API has operated.
    """
    assert search_query.facet_size({'facet_size': '2001'}) == 2000

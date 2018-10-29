"""Test dplaapi.suggestion_query"""

from unittest.mock import call
from dplaapi.queries import suggestion_query
from dplaapi.queries.suggestion_query import SuggestionQuery
from dplaapi.types import SuggestionQueryType


def test_SuggestionQuery_produces_correct_json_structure():
    params = SuggestionQueryType()
    params.update({'text': 'x'})
    q = SuggestionQuery(params).query
    assert isinstance(q['suggest'], dict)
    assert q['suggest']['text'] == 'x'
    assert isinstance(q['suggest']['sourceResource.title'], dict)
    assert isinstance(
        q['suggest']['sourceResource.title']['phrase']['collate'],
        dict)


def test_SuggestionQuery_calls_field_clause_correctly(mocker):
    params = SuggestionQueryType()
    params.update({'text': 'x'})
    mocker.spy(suggestion_query, 'field_clause')
    SuggestionQuery(params)
    calls = [call('sourceResource.title'), call('sourceResource.description')]
    suggestion_query.field_clause.assert_has_calls(calls)
    assert suggestion_query.field_clause.call_count == 2


def test_SuggestionQuery_collate_clause_is_called_correctly(mocker):
    params = SuggestionQueryType()
    params.update({'text': 'x'})
    mocker.spy(suggestion_query, 'collate_clause')
    SuggestionQuery(params)
    calls = [call('sourceResource.title'), call('sourceResource.description')]
    suggestion_query.collate_clause.assert_has_calls(calls)
    assert suggestion_query.collate_clause.call_count == 2

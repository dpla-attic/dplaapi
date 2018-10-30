"""Test dplaapi.suggestion_query"""

from unittest.mock import call
from dplaapi.queries import suggestion_query
from dplaapi.queries.suggestion_query import SuggestionQuery
from dplaapi.types import SuggestionQueryType


def test_SuggestionQuery_produces_correct_json_structure():
    params = SuggestionQueryType({'text': 'xx'})
    q = SuggestionQuery(params).query
    assert isinstance(q['suggest'], dict)
    assert q['suggest']['text'] == 'xx'
    assert isinstance(q['suggest']['sourceResource.title'], dict)


def test_SuggestionQuery_calls_field_clause_correctly(mocker):
    params = SuggestionQueryType({'text': 'xx'})
    mocker.spy(suggestion_query, 'field_clause')
    SuggestionQuery(params)
    calls = [call('sourceResource.title'), call('sourceResource.description')]
    suggestion_query.field_clause.assert_has_calls(calls)
    assert suggestion_query.field_clause.call_count == 2

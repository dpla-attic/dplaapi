"""Test dplaapi.lda_query"""

from dplaapi.queries.lda_query import LDAQuery
from dplaapi.types import LDAQueryType


def test_LDAQuery_produces_query_with_like_clause():
    """LDAQuery produces a query with a "vector" clause with an array of float"""
    params = LDAQueryType()
    params.update({'vector': ['0.1', '0.3']})
    q = LDAQuery(params)
    assert q.query['query']['script_score']['script']['params']['queryVector'] == [0.1, 0.3]


def test_LDAQuery_has_correct_default_sort():
    """The search query without a sort requested has the correct 'sort'"""
    params = LDAQueryType()
    params.update({'vector': ['0.1', '0.3']})
    q = LDAQuery(params)
    assert q.query['sort'] == [
        {'_score': {'order': 'desc'}},
        {'id': {'order': 'asc'}},
    ]

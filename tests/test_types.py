
"""Test dplaapi.types"""

from dplaapi import types


def test_items_query_type_is_match_all_true():
    """ItemsQueryType.match_all() is true when there are no query term
    parameters
    """
    params = types.ItemsQueryType(q=None)
    assert params.is_match_all()


def test_items_query_type_is_match_all_false():
    """ItemsQueryType.match_all() is false when there are query term
    parameters
    """
    params = types.ItemsQueryType(q='abcd')
    assert not params.is_match_all()

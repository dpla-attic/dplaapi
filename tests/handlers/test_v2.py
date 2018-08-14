"""Test dplaapi.handlers.v2"""

from dplaapi.handlers import v2


def test_items_query_type_is_match_all_false():
    """ItemsQueryType.match_all() is false when there are query parameters"""
    params = v2.ItemsQueryType(q='abcd')
    assert not params.is_match_all()


def test_items_query_type_is_match_all_true():
    """ItemsQueryType.match_all() is true when there are no query parameters"""
    params = v2.ItemsQueryType(q=None)
    assert params.is_match_all()

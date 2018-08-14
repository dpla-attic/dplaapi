
"""Test dplaapi.handlers.v2"""

import os
os.environ['ES_BASE'] = 'x'

import pytest
import requests
from dplaapi.handlers import v2 as v2_handlers


minimal_good_response = {
    'hits': [
        {'_source': {'sourceResource': {'title': 'x'}}}
    ]
}


class MockGoodResponse():
    """Mock a good `requests.Response`"""
    def raise_for_status(self):
        pass
    def json(self):
        return minimal_good_response


def mock_es_get_response_200(url):
    """Mock `requests.get()` for a successful request"""
    return MockGoodResponse()


def test_items_query_type_is_match_all_false():
    """ItemsQueryType.match_all() is false when there are query parameters"""
    params = v2_handlers.ItemsQueryType(q='abcd')
    assert not params.is_match_all()


def test_items_query_type_is_match_all_true():
    """ItemsQueryType.match_all() is true when there are no query parameters"""
    params = v2_handlers.ItemsQueryType(q=None)
    assert params.is_match_all()


@pytest.mark.asyncio
async def test_items_makes_es_request(monkeypatch):
    """items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'get', mock_es_get_response_200)
    result = await v2_handlers.items(q='abcd')
    assert result == minimal_good_response


"""Test dplaapi.handlers.v2"""

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


def mock_es_post_response_200(url, json):
    """Mock `requests.post()` for a successful request"""
    return MockGoodResponse()


@pytest.mark.asyncio
async def test_items_makes_es_request(monkeypatch):
    """items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    result = await v2_handlers.items(q='abcd')
    assert result == minimal_good_response

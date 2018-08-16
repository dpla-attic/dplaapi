
"""Test dplaapi.handlers.v2"""

import pytest
import requests
from apistar.exceptions import BadRequest
from apistar.http import QueryParams
from dplaapi.handlers import v2 as v2_handlers
from dplaapi.exceptions import ServerError
from dplaapi.search_query import SearchQuery


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


class Mock400Response():
    """Mock a `requests.Response` for an HTTP 400"""
    status_code = 400

    def raise_for_status(self):
        raise requests.exceptions.HTTPError('Can not parse whatever that was')


class Mock500Response():
    """Mock a `requests.Response` for an HTTP 500"""
    status_code = 500

    def raise_for_status(self):
        raise requests.exceptions.HTTPError('I have failed you.')


def mock_es_post_response_200(url, json):
    """Mock `requests.post()` for a successful request"""
    return MockGoodResponse()


def mock_es_post_response_400(url, json):
    """Mock `requests.post()` with a Bad Request response"""
    return Mock400Response()


def mock_es_post_response_err(url, json):
    """Mock `requests.post()` with a non-success status code"""
    return Mock500Response()


def mock_application_exception(*args, **kwargs):
    return {'impossible': 1/0}


@pytest.mark.asyncio
async def test_items_makes_es_request(monkeypatch):
    """items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = QueryParams({'q': 'abcd'})
    result = await v2_handlers.items(params)
    assert result == minimal_good_response


@pytest.mark.asyncio
async def test_items_raises_BadRequest_for_bad_param_value():
    """Input is validated and bad values for fields with constraints result in
    400 Bad Request responses"""
    params = QueryParams({'rights': "Not the URL it's supposed to be"})
    with pytest.raises(BadRequest):
        await v2_handlers.items(params)


@pytest.mark.asyncio
async def test_items_raises_BadRequest_for_unparseable_term(monkeypatch):
    """User input that is unparseable by Elasticsearch results in a 400"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    # Elasticsearch can not parse the following query term and responds with
    # an HTTP 400 Bad Request.
    params = QueryParams({'sourceResource.title': 'this AND AND that'})
    with pytest.raises(BadRequest) as excinfo:
        await v2_handlers.items(params)
    assert 'Invalid query' in str(excinfo)


@pytest.mark.asyncio
async def test_items_raises_ServerError_for_elasticsearch_errs(monkeypatch):
    """An Elasticsearch error response other than a 400 results in a 500"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    # Simulate some unsuccessful status code from Elasticsearch, other than a
    # 400 Bad Request.  Say a 500 Server Error, or a 404.
    params = QueryParams({'q': 'goodquery'})
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.items(params)
    assert 'Backend search operation failed' in str(excinfo)


@pytest.mark.asyncio
async def test_items_raises_ServerError_for_misc_app_exception(monkeypatch):
    """A bug in our application that raises an Exception results in
    a ServerError (HTTP 500) with a generic message"""
    monkeypatch.setattr(SearchQuery, '__init__', mock_application_exception)
    params = QueryParams({'q': 'goodquery'})
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.items(params)
    assert 'Unexpected error'in str(excinfo)


"""Test dplaapi.handlers.v2"""

import pytest
import requests
from apistar import test
from apistar.exceptions import BadRequest
from apistar.http import QueryParams
from dplaapi import app
from dplaapi import search_query
from dplaapi.handlers import v2 as v2_handlers
from dplaapi.exceptions import ServerError


client = test.TestClient(app)


minimal_good_response = {
    'took': 5,
    'timed_out': False,
    'shards': {'total': 3, 'successful': 3, 'skipped': 0, 'failed': 0},
    'hits': {
        'total': 1,
        'max_score': None,
        'hits': [
            {'_source': {'sourceResource': {'title': 'x'}}}
        ]
    }
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
    await v2_handlers.multiple_items(params)  # No error


@pytest.mark.asyncio
async def test_items_formats_response_metadata(monkeypatch):
    """items() assembles the correct response metadata"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = QueryParams({'q': 'abcd'})
    result = await v2_handlers.multiple_items(params)
    # See minimal_good_resonse above
    assert result['count'] == 1
    assert result['start'] == 1   # page 1; the default
    assert result['limit'] == 10  # the default
    assert result['docs'] == \
        [hit['_source'] for hit in minimal_good_response['hits']['hits']]


@pytest.mark.asyncio
async def test_items_raises_BadRequest_for_bad_param_value():
    """Input is validated and bad values for fields with constraints result in
    400 Bad Request responses"""
    params = QueryParams({'rights': "Not the URL it's supposed to be"})
    with pytest.raises(BadRequest):
        await v2_handlers.multiple_items(params)


@pytest.mark.asyncio
async def test_items_raises_BadRequest_for_unparseable_term(monkeypatch):
    """User input that is unparseable by Elasticsearch results in a 400"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    # Elasticsearch can not parse the following query term and responds with
    # an HTTP 400 Bad Request.
    params = QueryParams({'sourceResource.title': 'this AND AND that'})
    with pytest.raises(BadRequest) as excinfo:
        await v2_handlers.multiple_items(params)
    assert 'Invalid query' in str(excinfo)


@pytest.mark.asyncio
async def test_items_raises_ServerError_for_elasticsearch_errs(monkeypatch):
    """An Elasticsearch error response other than a 400 results in a 500"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    # Simulate some unsuccessful status code from Elasticsearch, other than a
    # 400 Bad Request.  Say a 500 Server Error, or a 404.
    params = QueryParams({'q': 'goodquery'})
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.multiple_items(params)
    assert 'Backend search operation failed' in str(excinfo)


@pytest.mark.asyncio
async def test_items_raises_ServerError_for_misc_app_exception(monkeypatch):
    """A bug in our application that raises an Exception results in
    a ServerError (HTTP 500) with a generic message"""
    monkeypatch.setattr(
        search_query.SearchQuery, '__init__', mock_application_exception)
    params = QueryParams({'q': 'goodquery'})
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.multiple_items(params)
    assert 'Unexpected error'in str(excinfo)


@pytest.mark.asyncio
async def test_items_handles_query_parameters(monkeypatch):
    """items() makes a good `goodparams' dict from querystring params"""
    def mock_searchquery(params_to_check):
        assert params_to_check == {'q': 'test'}
        return {}
    monkeypatch.setattr(search_query, 'SearchQuery', mock_searchquery)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = QueryParams({'q': 'test'})
    await v2_handlers.multiple_items(params)


@pytest.mark.asyncio
async def test_items_handles_string_parameter(monkeypatch):
    """items() makes a good `goodparams' dict from a single string parameter"""
    def mock_searchquery(params_to_check):
        assert params_to_check == {'id': '13283cd2bd45ef385aae962b144c7e6a'}
        return {}
    monkeypatch.setattr(search_query, 'SearchQuery', mock_searchquery)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    record_id = '13283cd2bd45ef385aae962b144c7e6a'
    await v2_handlers.single_item(record_id)


def test_multiple_items_path(monkeypatch):
    """/v2/items calls items() with query parameters object"""
    def mock_items_multiple(arg):
        assert isinstance(arg, QueryParams)
        return {}
    monkeypatch.setattr(v2_handlers, 'items', mock_items_multiple)
    client.get('/v2/items')


def test_single_item_path(monkeypatch):
    """/v2/items/{id} calls items() with a string"""
    def mock_items_single(arg):
        assert isinstance(arg, str)
        return {
            'count': 1,
            'start': 1,
            'limit': 10,
            'docs': [
                {
                    'id': '13283cd2bd45ef385aae962b144c7e6a',
                    'sourceResource': {'title': 'x'}
                }
            ]
        }
    monkeypatch.setattr(v2_handlers, 'items', mock_items_single)
    client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a')      # no error

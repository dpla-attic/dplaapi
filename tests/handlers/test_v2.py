
"""Test dplaapi.handlers.v2"""

import pytest
import requests
import json
import os
import boto3
import secrets
from starlette.testclient import TestClient
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.requests import Request
from starlette.background import BackgroundTask
from apistar.exceptions import ValidationError
from dplaapi.responses import JSONResponse
from dplaapi import app
from dplaapi import types, models
from dplaapi.handlers import v2 as v2_handlers
from dplaapi.queries import search_query
from dplaapi.queries.search_query import SearchQuery
import dplaapi.analytics
from peewee import OperationalError, DoesNotExist


client = TestClient(app,
                    base_url='http://localhost',
                    raise_server_exceptions=False)


minimal_good_response = {
    'took': 5,
    'timed_out': False,
    'shards': {'total': 3, 'successful': 3, 'skipped': 0, 'failed': 0},
    'hits': {
        'total': {'value': 1},
        'max_score': None,
        'hits': [
            {'_source': {'sourceResource': {'title': 'x'}}}
        ]
    }
}


minimal_necro_response = {
    'took': 5,
    'timed_out': False,
    'shards': {'total': 3, 'successful': 3, 'skipped': 0, 'failed': 0},
    'hits': {
        'total': {'value': 1},
        'max_score': None,
        'hits': [
            {'_source': {'id': '13283cd2bd45ef385aae962b144c7e6a'}}
        ]
    }
}


es6_facets = {
    'provider.name': {
        'doc_count_error_upper_bound': 169613,
        'sum_other_doc_count': 5893411,
        'buckets': [
            {
                'key': 'National Archives and Records Administration',
                'doc_count': 3781862
            }
        ]
    },
    "sourceResource.date.begin.year": {
        "doc_count": 14,
        "sourceResource.date.begin.year": {
            "buckets": [
                {
                    "key_as_string": "1947",
                    "key": -725846400000,
                    "doc_count": 1
                }
            ]
        }
    },
    'sourceResource.spatial.coordinates': {
        'buckets': [
            {
                'key': '*-99.0',
                'from': 0,
                'to': 99,
                'doc_count': 518784
            }
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


class Mock404Response():
    """Mock a `requests.Response` for an HTTP 404"""
    status_code = 404

    def raise_for_status(self):
        raise requests.exceptions.HTTPError('Index not found')


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


def mock_es_post_response_404(url, json):
    """Mock `requests.post()` with a Not Found response"""
    return Mock404Response()


def mock_es_post_response_err(url, json):
    """Mock `requests.post()` with a non-success status code"""
    return Mock500Response()


def mock_Account_get(*args, **kwargs):
    return models.Account(key='08e3918eeb8bf4469924f062072459a8',
                          email='x@example.org',
                          enabled=True)


def mock_disabled_Account_get(*args, **kwargs):
    return models.Account(key='08e3918eeb8bf4469924f062072459a8',
                          email='x@example.org',
                          enabled=False)


def mock_not_found_Account_get(*args, **kwargs):
    raise DoesNotExist()


def mock_search_necro_w_no_results(*args, **kwargs):
    return {'hits': {'total': {'value': 0}}}


def get_request(path, querystring=None, path_params=None):
    rv = {'type': 'http', 'method': 'GET', 'path': path, 'query_string': b''}
    if querystring:
        rv['query_string'] = querystring.encode('utf-8')
    if path_params:
        rv['path_params'] = path_params
    return Request(rv)


def post_request(path, path_params=None):
    rv = {'type': 'http', 'method': 'POST', 'path': path}
    if path_params:
        rv['path_params'] = path_params
    return Request(rv)


@pytest.fixture(scope='function')
def disable_auth():
    os.environ['DISABLE_AUTH'] = 'true'
    yield
    del(os.environ['DISABLE_AUTH'])


@pytest.fixture(scope='function')
def patch_db_connection(monkeypatch):

    def mock_db_connect():
        return True

    def mock_db_close():
        return True

    monkeypatch.setattr(models.db, 'connect', mock_db_connect)
    monkeypatch.setattr(models.db, 'close', mock_db_close)
    yield


@pytest.fixture(scope='function')
def patch_bad_db_connection(monkeypatch):

    def mock_db_connect(*args, **kwargs):
        raise OperationalError()

    def mock_db_close():
        return True

    monkeypatch.setattr(models.db, 'connect', mock_db_connect)
    monkeypatch.setattr(models.db, 'close', mock_db_close)
    yield


@pytest.fixture(scope='function')
def disable_api_key_check(monkeypatch, mocker):
    acct_stub = mocker.stub()
    monkeypatch.setattr(v2_handlers, 'account_from_params', acct_stub)
    yield


@pytest.fixture(scope='function')
def stub_tracking(monkeypatch, mocker):
    track_stub = mocker.stub()
    monkeypatch.setattr(dplaapi.analytics, 'track', track_stub)


# account_from_params() tests ...


@pytest.mark.usefixtures('patch_db_connection')
def test_account_from_params_queries_account(monkeypatch, mocker):
    """It connects to the database and retrieves the Account"""
    mocker.patch('dplaapi.models.db.connect')
    monkeypatch.setattr(models.Account, 'get', mock_Account_get)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = {
        'api_key': '08e3918eeb8bf4469924f062072459a8',
        'from': 0,
        'page': 1,
        'page_size': 1
    }
    v2_handlers.account_from_params(params)
    models.db.connect.assert_called_once()


@pytest.mark.usefixtures('patch_db_connection')
def test_account_from_params_returns_for_disabled_acct(monkeypatch, mocker):
    """It returns HTTP 403 Forbidden if the Account is disabled"""
    mocker.patch('dplaapi.models.db.connect')
    monkeypatch.setattr(models.Account, 'get', mock_disabled_Account_get)
    params = {
        'api_key': '08e3918eeb8bf4469924f062072459a8',
        'from': 0,
        'page': 1,
        'page_size': 1
    }
    with pytest.raises(HTTPException) as e:
        v2_handlers.account_from_params(params)
        assert e.status_code == 403


@pytest.mark.usefixtures('patch_db_connection')
def test_account_from_params_bad_api_key(monkeypatch, mocker):
    """It returns HTTP 403 Forbidden if the Account is disabled"""
    mocker.patch('dplaapi.models.db.connect')
    monkeypatch.setattr(models.Account, 'get', mock_not_found_Account_get)
    params = {
        'api_key': '08e3918eeb8bf4469924f062072459a8',
        'from': 0,
        'page': 1,
        'page_size': 1
    }
    with pytest.raises(HTTPException) as e:
        v2_handlers.account_from_params(params)
        assert e.status_code == 403


@pytest.mark.usefixtures('patch_bad_db_connection')
def test_account_from_params_ServerError_bad_db(monkeypatch, mocker):
    """It returns Service Unavailable if it can't connect to the database"""
    params = {
        'api_key': '08e3918eeb8bf4469924f062072459a8',
        'from': 0,
        'page': 1,
        'page_size': 1
    }
    with pytest.raises(HTTPException) as e:
        v2_handlers.account_from_params(params)
        assert e.status_code == 503


# end account_from_params() tests


# items() tests ...


@pytest.mark.usefixtures('disable_auth')
def test_items_makes_es_request(monkeypatch):
    """multiple_items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    sq = SearchQuery({'q': 'abcd', 'from': 0, 'page': 1, 'page_size': 1})
    v2_handlers.items(sq)  # No error


@pytest.mark.usefixtures('disable_auth')
def test_items_Exception_for_elasticsearch_errs(monkeypatch):
    """An Elasticsearch error response other than a 400 results in a 500"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    # Simulate some unsuccessful status code from Elasticsearch, other than a
    # 400 Bad Request.  Say a 500 Server Error, or a 404.
    sq = SearchQuery({'q': 'goodquery', 'from': 0, 'page': 1, 'page_size': 1})
    with pytest.raises(Exception):
        v2_handlers.items(sq)


# multiple_items() tests ...


@pytest.mark.usefixtures('disable_auth')
def test_multiple_items_calls_search_items_correctly(monkeypatch):
    """/v2/items calls search_items() with dictionary"""
    def mock_items(arg):
        assert isinstance(arg, dict)
        return minimal_good_response
    monkeypatch.setattr(v2_handlers, 'search_items', mock_items)
    client.get('/v2/items')


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
@pytest.mark.usefixtures('stub_tracking')
async def test_multiple_items_formats_response_metadata(monkeypatch, mocker):
    """multiple_items() assembles the correct response metadata"""

    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    request = get_request('/v2/items', 'q=abcd')
    response_obj = await v2_handlers.multiple_items(request)
    result = json.loads(response_obj.body)

    # See minimal_good_response above
    assert result['count'] == 1
    assert result['start'] == 1   # page 1; the default
    assert result['limit'] == 10  # the default
    assert result['docs'] == \
        [hit['_source'] for hit in minimal_good_response['hits']['hits']]


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
async def test_multiple_items_handles_query_parameters(monkeypatch, mocker):
    """multiple_items() makes a good `goodparams' from querystring params"""
    def mock_searchquery(params_to_check):
        assert params_to_check == {'q': 'test'}
        return {}
    monkeypatch.setattr(search_query, 'SearchQuery', mock_searchquery)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    request = get_request('/v2/items', 'q=test')
    await v2_handlers.multiple_items(request)


@pytest.mark.asyncio
async def test_multiple_items_calls_BackgroundTask(monkeypatch,
                                                   mocker):
    """It instantiates BackgroundTask correctly"""

    def mock_items(*args):
        return minimal_good_response

    def mock_account(*args):
        return models.Account(id=1, key='a1b2c3', email='x@example.org')

    def mock_background_task(*args, **kwargs):
        # __init__() has to return None, so this is not a mocker.stub()
        return None

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    monkeypatch.setattr(BackgroundTask, '__init__', mock_background_task)
    mocker.spy(BackgroundTask, '__init__')

    request = get_request('/v2/items', 'q=test')
    ok_data = {
        'count': 1,
        'start': 1,
        'limit': 10,
        'docs': [{'sourceResource': {'title': 'x'}}],
        'facets': []
    }

    await v2_handlers.multiple_items(request)
    BackgroundTask.__init__.assert_called_once_with(
        mocker.ANY, mocker.ANY, request=mocker.ANY, results=ok_data,
        api_key='a1b2c3', title='Item search results')


@pytest.mark.asyncio
async def test_multiple_items_strips_lone_star_vals(monkeypatch, mocker):

    def mock_items(*argv):
        return minimal_good_response

    def mock_account(*argv):
        return models.Account(key='a1b2c3', email='x@example.org')

    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    monkeypatch.setattr(v2_handlers, 'search_items', mock_items)
    mocker.spy(v2_handlers, 'search_items')

    # 'q' should be stripped out because it is just '*'
    request = get_request('/v2/items', 'q=*')

    await v2_handlers.multiple_items(request)
    v2_handlers.search_items.assert_called_once_with(
        {'page': 1, 'page_size': 10, 'sort_order': 'asc'})


# end multiple_items tests.


# mlt tests ...

@pytest.mark.usefixtures('disable_auth')
def test_mlt_calls_mlt_items_correctly(monkeypatch):
    """/v2/items/<item>/mlt calls mlt_items with dictionary"""
    def mock_items(arg):
        assert isinstance(arg, dict)
        return minimal_good_response
    monkeypatch.setattr(v2_handlers, 'mlt_items', mock_items)
    client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a/mlt')


@pytest.mark.usefixtures('disable_auth')
@pytest.mark.usefixtures('stub_tracking')
def test_mlt_formats_response_metadata(monkeypatch, mocker):
    """mlt_items() assembles the correct response metadata"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    response = client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a/mlt')
    result = response.json()

    # See minimal_good_response above
    assert result['count'] == 1
    assert result['start'] == 1
    assert result['limit'] == 10
    assert result['docs'] == \
        [hit['_source'] for hit in minimal_good_response['hits']['hits']]


@pytest.mark.usefixtures('disable_auth')
def test_mlt_returns_bad_request_err_for_bad_id(monkeypatch, mocker):
    """It raises a Bad Request error for a badly-formatted record ID"""
    response = client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a,x/mlt')
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mlt_calls_track_w_correct_params(monkeypatch, mocker):
    """It calls dplaapi.analytics.track() correctly"""

    def mock_items(*argv):
        return minimal_good_response

    def mock_account(*argv):
        return models.Account(key='a1b2c3', email='x@example.org')

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    track_stub = mocker.stub(name='track_stub')
    monkeypatch.setattr(v2_handlers, 'track', track_stub)

    path_params = {'id_or_ids': '13283cd2bd45ef385aae962b144c7e6a'}
    request = get_request('/v2/items/13283cd2bd45ef385aae962b144c7e6a/mlt',
                          path_params=path_params)

    ok_data = {
        'count': 1,
        'start': 1,
        'limit': 10,
        'docs': [{'sourceResource': {'title': 'x'}}]
    }

    await v2_handlers.mlt(request)
    track_stub.assert_called_once_with(request, ok_data, 'a1b2c3',
                                       'More-Like-This search results')


@pytest.mark.usefixtures('disable_auth')
def test_mlt_rejects_invalid_params(monkeypatch, mocker):
    """The MLT handler rejects parameters of the regular search that are
    irrelevant to More-Like-This and gives a clear message about the
    parameter being invalid.
    """
    search_param_keys = set(types.items_params.keys())
    mlt_param_keys = set(types.mlt_params.keys())
    bad_params = search_param_keys - mlt_param_keys
    for param in bad_params:
        path = '/v2/items/13283cd2bd45ef385aae962b144c7e6a/mlt?%s=x' % param
        response = client.get(path)
        assert response.status_code == 400
        assert 'is not a valid parameter' in response.json()

# end mlt tests.


# specific_items tests ...


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_passes_ids(monkeypatch, mocker):
    """specific_item() calls search_items() with correct 'ids' parameter"""

    def mock_search_items(*args):
        return minimal_good_response

    monkeypatch.setattr(v2_handlers, 'search_items', mock_search_items)
    monkeypatch.setattr(v2_handlers, 'search_necro',
                        mock_search_necro_w_no_results)
    mocker.spy(v2_handlers, 'search_items')
    path_params = {'id_or_ids': '13283cd2bd45ef385aae962b144c7e6a'}
    request = get_request('/v2/items/13283cd2bd45ef385aae962b144c7e6a',
                          path_params=path_params)

    await v2_handlers.specific_item(request)

    v2_handlers.search_items.assert_called_once_with(
        {'page': 1, 'page_size': 1, 'sort_order': 'asc',
         'ids': ['13283cd2bd45ef385aae962b144c7e6a']})


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_passes_ids_to_necropolis(monkeypatch, mocker):
    """specific_item() calls search_items() with correct 'ids' parameter"""

    def mock_search_items(*args):
        return minimal_good_response

    def mock_search_necro(*args):
        return minimal_necro_response

    monkeypatch.setattr(v2_handlers, 'search_items', mock_search_items)
    monkeypatch.setattr(v2_handlers, 'search_necro', mock_search_necro)
    mocker.spy(v2_handlers, 'search_necro')
    path_params = {'id_or_ids': '13283cd2bd45ef385aae962b144c7e6a'}
    request = get_request('/v2/items/13283cd2bd45ef385aae962b144c7e6a',
                          path_params=path_params)

    await v2_handlers.specific_item(request)

    v2_handlers.search_necro.assert_called_once_with(
        {'page': 1, 'page_size': 1, 'sort_order': 'asc',
         'ids': ['13283cd2bd45ef385aae962b144c7e6a']})


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_handles_multiple_ids(monkeypatch, mocker):
    """It splits ids on commas and calls search_items() with a list of those
    IDs
    """
    def mock_search_items(arg):
        assert len(arg['ids']) == 2
        return minimal_good_response

    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867a39cac531e13a48c1'
    monkeypatch.setattr(v2_handlers, 'search_items', mock_search_items)
    monkeypatch.setattr(v2_handlers, 'search_necro',
                        mock_search_necro_w_no_results)
    path_params = {'id_or_ids': ids}
    request = get_request("/v2/items/%s" % ids, path_params=path_params)

    await v2_handlers.specific_item(request)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_ids_1(mocker):
    path_params = {'id_or_ids': 'x'}
    request = get_request('/v2/items/x', path_params=path_params)
    with pytest.raises(HTTPException) as e:
        await v2_handlers.specific_item(request)
        assert e.status_code == 400


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_ids_2(mocker):
    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867'
    path_params = {'id_or_ids': ids}
    request = get_request("/v2/items/%s" % ids, path_params=path_params)
    with pytest.raises(HTTPException) as e:
        await v2_handlers.specific_item(request)
        assert e.status_code == 400


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_accepts_callback_querystring_param(monkeypatch,
                                                                mocker):

    def mock_items(arg):
        return minimal_good_response

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    monkeypatch.setattr(v2_handlers, 'search_necro',
                        mock_search_necro_w_no_results)
    ids = '13283cd2bd45ef385aae962b144c7e6a'
    path_params = {'id_or_ids': ids}
    query_string = 'callback=f'
    request = get_request("/v2/items/%s" % ids,
                          path_params=path_params,
                          querystring=query_string)
    await v2_handlers.specific_item(request)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_querystring_param(mocker):

    ids = '13283cd2bd45ef385aae962b144c7e6a'
    path_params = {'id_or_ids': ids}
    query_string = 'page_size=1'
    request = get_request("/v2/items/%s" % ids,
                          path_params=path_params,
                          querystring=query_string)
    with pytest.raises(HTTPException) as e:
        await v2_handlers.specific_item(request)
        assert e.status_code == 400


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_NotFound_for_zero_hits(monkeypatch, mocker):
    """It raises a Not Found if there are no documents"""

    def mock_zero_items(*args):
        return {'hits': {'total': {'value': 0}}}

    monkeypatch.setattr(v2_handlers, 'items', mock_zero_items)

    ids = '13283cd2bd45ef385aae962b144c7e6a'
    path_params = {'id_or_ids': ids}
    request = get_request("/v2/items/%s" % ids, path_params=path_params)

    with pytest.raises(HTTPException) as e:
        await v2_handlers.specific_item(request)
        assert e.status_code == 404


@pytest.mark.asyncio
async def test_specific_item_calls_BackgroundTask(monkeypatch,
                                                  mocker):
    """It instantiates BackgroundTask correctly"""

    def mock_items(*argv):
        return minimal_good_response

    def mock_account(*argv):
        return models.Account(id=1, key='a1b2c3', email='x@example.org')

    def mock_background_task(*args, **kwargs):
        # __init__() has to return None, so this is not a mocker.stub()
        return None

    monkeypatch.setattr(v2_handlers, 'search_items', mock_items)
    monkeypatch.setattr(v2_handlers, 'search_necro',
                        mock_search_necro_w_no_results)
    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    monkeypatch.setattr(BackgroundTask, '__init__', mock_background_task)
    mocker.spy(BackgroundTask, '__init__')

    ok_data = {
        'count': 1,
        'inactive_count': 0,
        'docs': [{'sourceResource': {'title': 'x'}}],
        'inactive_docs': []
    }

    ids = '13283cd2bd45ef385aae962b144c7e6a'
    path_params = {'id_or_ids': ids}
    request = get_request("/v2/items/%s" % ids, path_params=path_params)

    await v2_handlers.specific_item(request)
    BackgroundTask.__init__.assert_called_once_with(
        mocker.ANY, mocker.ANY, request=mocker.ANY, results=ok_data,
        api_key='a1b2c3', title='Fetch items')


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
@pytest.mark.usefixtures('stub_tracking')
async def test_specific_items_formats_response_metadata(monkeypatch, mocker):
    """specific_items() assembles the correct response metadata"""

    def mock_items(*argv):
        return minimal_good_response

    def mock_necro(*argv):
        return minimal_necro_response

    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    monkeypatch.setattr(v2_handlers, 'search_items', mock_items)
    monkeypatch.setattr(v2_handlers, 'search_necro', mock_necro)

    ids = '13283cd2bd45ef385aae962b144c7e6a'
    path_params = {'id_or_ids': ids}
    request = get_request("/v2/items/%s" % ids, path_params=path_params)
    response_obj = await v2_handlers.specific_item(request)
    result = json.loads(response_obj.body)

    # See minimal_good_response above
    assert result['count'] == 1
    assert result['inactive_count'] == 1
    assert result['docs'] == \
           [hit['_source'] for hit in minimal_good_response['hits']['hits']]
    assert result['inactive_docs'] == \
           [hit['_source'] for hit in minimal_necro_response['hits']['hits']]


# end specific_items tests.


# begin api_key and related tests

class MockBoto3Client():
    def send_email(*args):
        pass


def mock_boto3_client_factory(*args):
    return MockBoto3Client()


def test_send_email_uses_correct_source_and_destination(monkeypatch, mocker):
    """It makes the boto3 send_email call with the right parameters"""
    from_email = 'testfrom@example.org'
    to_email = 'testto@example.org'

    monkeypatch.setenv('EMAIL_FROM', from_email)
    monkeypatch.setattr(boto3, 'client', mock_boto3_client_factory)
    send_email_stub = mocker.stub()
    monkeypatch.setattr(MockBoto3Client, 'send_email', send_email_stub)

    v2_handlers.send_email('x', to_email)
    send_email_stub.assert_called_once_with(
        Destination={'ToAddresses': ['testto@example.org']},
        Message='x',
        Source='testfrom@example.org')


def test_send_email_raises_ServerError_for_no_EMAIL_FROM(monkeypatch, mocker):
    """It raises Server Error when the EMAIL_FROM env. var. is undefined"""
    monkeypatch.delenv('EMAIL_FROM', raising=False)
    with pytest.raises(HTTPException) as e:
        v2_handlers.send_email('x', 'testto@example.org')
        assert e.status_code == 500


def test_send_api_key_email_calls_send_email_w_correct_params(monkeypatch,
                                                              mocker):
    """It calls send_email() with the correct parameters"""
    send_email_stub = mocker.stub()
    monkeypatch.setattr(v2_handlers, 'send_email', send_email_stub)
    v2_handlers.send_api_key_email('x@example.org', 'a1b2c3')
    send_email_stub.assert_called_once_with(
        {
            'Body': {
                'Text': {
                    'Data': 'Your API key is a1b2c3'
                }
            },
            'Subject': {'Data': 'Your new DPLA API key'}
        },
        'x@example.org'
    )


def test_send_api_key_email_raises_ServerError_for_Exception(monkeypatch):
    def buggy_send_email(*args):
        1/0

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(HTTPException) as e:
        v2_handlers.send_api_key_email('x@example.org', 'a1b2c3')
        assert e.status_code == 500


def test_send_api_key_email_reraises_HTTPException(monkeypatch):
    def buggy_send_email(*args):
        raise HTTPException(404)

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(HTTPException) as e:
        v2_handlers.send_api_key_email('x@example.org', 'a1b2c3')
        assert e.status_code == 404


def test_send_reminder_email_calls_send_email_w_correct_params(monkeypatch,
                                                               mocker):
    """It calls send_email with the correct parameters."""
    send_email_stub = mocker.stub()
    monkeypatch.setattr(v2_handlers, 'send_email', send_email_stub)
    v2_handlers.send_reminder_email('x@example.org', 'a1b2c3')
    send_email_stub.assert_called_once_with(
        {
            'Body': {
                'Text': {
                    'Data': 'The most recent API key for x@example.org '
                            'is a1b2c3'
                }
            },
            'Subject': {'Data': 'Your existing DPLA API key'}
        },
        'x@example.org'
    )


def test_send_reminder_email_raises_Server_Error_for_Exception(monkeypatch):
    def buggy_send_email(*args):
        1/0

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(HTTPException) as e:
        v2_handlers.send_reminder_email('x@example.org', 'a1b2c3')
        assert e.status_code == 500


def test_send_reminder_email_reraises_HTTPException(monkeypatch):
    def buggy_send_email(*args):
        raise HTTPException(404)

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(HTTPException) as e:
        v2_handlers.send_reminder_email('x@example.org', 'a1b2c3')
        assert e.status_code == 404


@pytest.mark.asyncio
async def test_api_key_flunks_bad_email():
    """api_key() rejects an obviously malformed email address"""
    # But only the most obvious cases involving misplaced '@' or lack of '.'
    bad_addrs = ['f@@ey', '56b7165e4f8a54b4faf1e04c46a6145c']
    for addr in bad_addrs:
        path_params = {'email': addr}
        request = post_request("/v2/api_key/%s" % addr,
                               path_params=path_params)
        with pytest.raises(HTTPException) as e:
            await v2_handlers.api_key(request)
            assert e.status_code == 400


@pytest.mark.asyncio
@pytest.mark.usefixtures('patch_db_connection')
async def test_api_key_bails_if_account_exists_for_email(monkeypatch, mocker):
    """api_key() quits and sends a reminder email if there's already an Account
    for the given email"""
    def mock_get(*args, **kwargs):
        return models.Account(email='x@example.org',
                              key='08e3918eeb8bf4469924f062072459a8')

    monkeypatch.setattr(models.Account, 'get', mock_get)
    stub = mocker.stub()
    monkeypatch.setattr(v2_handlers, 'send_reminder_email', stub)
    request = post_request("/v2/api_key/x@example.org",
                           path_params={'email': 'x@example.org'})
    with pytest.raises(HTTPException) as e:
        await v2_handlers.api_key(request)
        assert e.status_code == 409

    stub.assert_called_once_with('x@example.org',
                                 '08e3918eeb8bf4469924f062072459a8')


@pytest.mark.asyncio
@pytest.mark.usefixtures('patch_bad_db_connection')
async def test_api_key_raises_503_for_bad_db_connection(monkeypatch,
                                                        mocker):
    """api_key() raises ServerError if it can't connect to the database"""
    with pytest.raises(HTTPException) as e:
        request = post_request("/v2/api_key/x@example.org",
                               path_params={'email': 'x@example.org'})
        await v2_handlers.api_key(request)
        assert e.status_code == 503


# Fixture for the following two tests
@pytest.fixture(scope='function')
def good_api_key_invocation(monkeypatch, mocker):

    def mock_token_hex(*args):
        return '08e3918eeb8bf4469924f062072459a8'

    def mock_get(*args, **kwargs):
        raise DoesNotExist()

    class AtomicContextMgr(object):
        def __enter__(self):
            pass

        def __exit__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(secrets, 'token_hex', mock_token_hex)
    monkeypatch.setattr(models.Account, 'get', mock_get)
    send_email_stub = mocker.stub()
    monkeypatch.setattr(v2_handlers, 'send_api_key_email', send_email_stub)
    save_stub = mocker.stub()
    monkeypatch.setattr(models.Account, 'save', save_stub)
    monkeypatch.setattr(models.db, 'atomic', AtomicContextMgr)
    yield


@pytest.mark.asyncio
@pytest.mark.usefixtures('patch_db_connection')
@pytest.mark.usefixtures('good_api_key_invocation')
async def test_api_key_creates_account(monkeypatch, mocker):
    """api_key() creates a new Account record & defines the right fields"""

    mocker.spy(models.Account, '__init__')

    request = post_request("/v2/api_key/x@example.org",
                           path_params={'email': 'x@example.org'})
    await v2_handlers.api_key(request)

    models.Account.__init__.assert_called_with(
        mocker.ANY,
        key='08e3918eeb8bf4469924f062072459a8',
        email='x@example.org',
        enabled=True)


# end api_key tests


def test_geo_facets():
    result = v2_handlers.geo_facets(
        es6_facets['sourceResource.spatial.coordinates'])
    assert result == {
        '_type': 'geo_distance',
        'ranges': [{'from': 0, 'to': 99, 'count': 518784}]
    }


def test_date_facets():
    result = v2_handlers.date_facets(
        es6_facets['sourceResource.date.begin.year'])
    assert result == {
        '_type': 'date_histogram',
        'entries': [{'time': '1947', 'count': 1}]
    }


def test_term_facets():
    result = v2_handlers.term_facets(
        es6_facets['provider.name'])
    assert result == {
        '_type': 'terms',
        'terms': [
            {
                'term': 'National Archives and Records Administration',
                'count': 3781862
            }
        ]
    }


def test_formatted_facets():
    """It makes the necessary function calls and dictionary lookups to
    construct and return a correct dict"""
    assert v2_handlers.formatted_facets(es6_facets) == {
        'provider.name': {
            '_type': 'terms',
            'terms': [
                {
                    'term': 'National Archives and Records Administration',
                    'count': 3781862
                }
            ]
        },
        'sourceResource.date.begin.year': {
            '_type': 'date_histogram',
            'entries': [
                {
                    'time': '1947',
                    'count': 1
                }
            ]
        },
        'sourceResource.spatial.coordinates': {
            '_type': 'geo_distance',
            'ranges': [
                {
                    'from': 0,
                    'to': 99,
                    'count': 518784
                }
            ]
        }
    }


def test_formatted_facets_returns_empty_list_for_no_facets():
    """It returns an empty list, not a dict, for no facets!"""
    assert v2_handlers.formatted_facets({}) == []   # sigh.


def test_dict_with_date_buckets_works_with_ranges_aggregation():
    """It picks the 'buckets' out of an aggregation response for a range
    aggregation"""
    es_result_agg = {
        'buckets': [
            {
                'key': '1520-1529',
                'from': -14200704000000,
                'from_as_string': '1520',
                'to': -13916620800000,
                'to_as_string': '1529',
                'doc_count': 0
            }
        ]
    }
    result = v2_handlers.dict_with_date_buckets(es_result_agg)
    assert type(result) == list


def test_dict_with_date_buckets_works_with_histogram_aggregation():
    """It picks the 'buckets' out of an aggregation response for a histogram
    aggregation with our 'filter' clause"""
    es_result_agg = {
        'doc_count': 14,
        'sourceResource.date.begin.year': {
            'buckets': [
                {
                    'key_as_string': '1947',
                    'key': -725846400000,
                    'doc_count': 1
                }
            ]
        }
    }
    result = v2_handlers.dict_with_date_buckets(es_result_agg)
    assert type(result) == list


def test_dict_with_date_buckets_raises_exception_with_weird_aggregation():
    """It raises an Exception if it gets weird data without a 'buckets'
    property"""
    es_result_agg = {
        'doc_count': 14,
        'x': 'x'
    }
    with pytest.raises(Exception):
        v2_handlers.dict_with_date_buckets(es_result_agg)


def test_response_object_returns_JSONResponse_for_typical_request():
    """It returns an apistar.http.JSONResponse object for a typical request,
    without a JSONP callback"""
    rv = v2_handlers.response_object({}, {})
    assert isinstance(rv, JSONResponse)


def test_response_object_returns_correct_Response_for_JSONP_request():
    """It returns an apistar.http.JSONResponse object for a typical request,
    without a JSONP callback"""
    rv = v2_handlers.response_object({}, {'callback': 'f'})
    assert isinstance(rv, Response)
    assert rv.headers['content-type'] \
        == 'application/javascript; charset=utf-8'
    assert rv.body == b'f({})'


# Exception-handling and HTTP status double-checks


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_500_means_client_503(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    response = client.get('/v2/items')
    assert response.status_code == 503
    assert response.json() == 'Backend search operation failed'


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_400_means_client_400(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    response = client.get('/v2/items?q=some+bad+search')
    assert response.status_code == 400
    assert response.json() == 'Invalid query'


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_404_means_client_503(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_404)
    response = client.get('/v2/items')
    assert response.status_code == 503
    assert response.json() == 'Backend search operation failed'


@pytest.mark.usefixtures('disable_api_key_check')
def test_ItemsQueryType_ValidationError_means_client_400(monkeypatch):

    def badinit(*args, **kwargs):
        raise ValidationError('no good')

    monkeypatch.setattr(types.ItemsQueryType, '__init__', badinit)
    response = client.get('/v2/items?hasView.format=some+bad+string')
    assert response.status_code == 400


@pytest.mark.usefixtures('disable_api_key_check')
def test_ItemsQueryType_Exception_means_client_500(monkeypatch):

    def badinit(*args, **kwargs):
        raise AttributeError()

    monkeypatch.setattr(types.ItemsQueryType, '__init__', badinit)
    response = client.get('/v2/items?provider.name=a+provider')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


@pytest.mark.usefixtures('disable_auth')
def test_search_query_Exception_means_client_500(monkeypatch):

    def problem_func(*args, **kwargs):
        raise KeyError()

    monkeypatch.setattr(SearchQuery, '__init__', problem_func)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_compact_with_dotted_field_param():
    """compact() takes an ES 6 "doc" and compacts the keys so that they look
    like they used to coming out of ES 0.90"""
    before = {
        'id': '00000134adfdfa05e988480f9fa56b1a',
        'sourceResource': {
            'date': {
                'begin': '1990',
                'end': '1991'
            }
        }
    }
    after = {
        'id': '00000134adfdfa05e988480f9fa56b1a',
        'sourceResource.date': {
            'begin': '1990',
            'end': '1991'
        }
    }
    result = v2_handlers.compact(before.copy(),
                                 {'fields': 'id,sourceResource.date'})
    assert result == after


def test_compact_without_toplevel_field_param():
    """compact() does not flatten fields if we're returning the whole
    sourceResource"""
    before = {
        'id': '00000134adfdfa05e988480f9fa56b1a',
        'sourceResource': {
            'title': 'x',
            'date': {
                'begin': '1990',
                'end': '1991'
            }
        }
    }
    result = v2_handlers.compact(before.copy(),
                                 {'fields': 'id,sourceResource'})
    assert result == before


def test_compact_handles_missing_fields():
    """compact() handles documents that don't have the requested field"""
    before = {
        'id': '00000134adfdfa05e988480f9fa56b1a',
        'sourceResource': {
            'title': 'x'
        }
    }
    after = {
        'id': '00000134adfdfa05e988480f9fa56b1a',
        'sourceResource.title': 'x'
    }
    params = {
        'fields': 'id,sourceResource.title,sourceResource.date'
    }
    result = v2_handlers.compact(before.copy(), params)
    assert result == after


def test_items_key():
    params = {'api_key': 'a1b2c3', 'ids': ['e5', 'd4']}
    result = v2_handlers.items_key(params)
    # Note that 'ids' is sorted
    assert result == (('api_key', 'a1b2c3'), ('ids', 'd4,e5'), 'v2_items')


def test_traverse_doc_handles_strings():
    path = 'sourceResource.language.name'
    doc = {'sourceResource': {'language': {'name': 'English'}}}
    result = v2_handlers.traverse_doc(path, doc)
    assert result == 'English'


def test_traverse_doc_handles_lists_1():
    path = 'sourceResource.language.name'
    doc = {'sourceResource': {'language': [{'name': 'English'}]}}
    result = v2_handlers.traverse_doc(path, doc)
    assert result == 'English'


def test_traverse_doc_handles_lists_2():
    path = 'sourceResource.language.name'
    doc = {
        'sourceResource': {
            'language': [{'name': 'English'}, {'name': 'Spanish'}]
        }
    }
    result = v2_handlers.traverse_doc(path, doc)
    assert result == ['English', 'Spanish']


def test_traverse_doc_handles_nested_arrays_and_objects():
    path = 'a.b.c.d'
    doc = {'a': {'b': [{'c': [{'d': 'the value'}]}]}}
    result = v2_handlers.traverse_doc(path, doc)
    assert result == 'the value'


def test_traverse_doc_handles_nonexistent_field_1():
    path = 'a.b.c.d'
    doc = {'a': {'b': [{'foo': 'x'}]}}
    result = v2_handlers.traverse_doc(path, doc)
    assert result is None


def test_traverse_doc_handles_nonexistent_field_2():
    path = 'a.b'
    doc = {'a': 'x'}
    result = v2_handlers.traverse_doc(path, doc)
    assert result is None


def test_traverse_doc_handles_empty_list():
    path = 'a'
    doc = {'a': []}
    result = v2_handlers.traverse_doc(path, doc)
    assert result is None


def test_traverse_doc_handles_object():
    path = 'a'
    doc = {'a': {'b': 'c'}}
    result = v2_handlers.traverse_doc(path, doc)
    assert result == {'b': 'c'}


def test_flatten():
    li = ['a', 'b']
    rv = [x for x in v2_handlers.flatten(li)]
    assert rv == ['a', 'b']

    li = ['a', ['b', 'c']]
    rv = [x for x in v2_handlers.flatten(li)]
    assert rv == ['a', 'b', 'c']

    li = ['a', ['b', ['c', 'd']]]
    rv = [x for x in v2_handlers.flatten(li)]
    assert rv == ['a', 'b', 'c', 'd']

    rv = [x for x in v2_handlers.flatten(None)]
    assert rv == []

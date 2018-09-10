
"""Test dplaapi.handlers.v2"""

import pytest
import requests
import json
import os
import boto3
import secrets
from apistar import test
from apistar.exceptions import Forbidden, NotFound, BadRequest, ValidationError
from apistar.http import QueryParams, Response, JSONResponse
from dplaapi import app
from dplaapi import search_query, types, models
from dplaapi.handlers import v2 as v2_handlers
from dplaapi.exceptions import ServerError, ConflictError
import dplaapi.analytics
from peewee import OperationalError, DoesNotExist


client = test.TestClient(app, hostname='localhost')


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
    "sourceResource.date.begin.decade": {
        "buckets": [
            {
                "key": "1520-1529",
                "from": -14200704000000,
                "from_as_string": "1520",
                "to": -13916620800000,
                "to_as_string": "1529",
                "doc_count": 10
            }
        ]
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


def mock_application_exception(*args, **kwargs):
    return {'impossible': 1/0}


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
    with pytest.raises(Forbidden):
        v2_handlers.account_from_params(params)


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
    with pytest.raises(Forbidden):
        v2_handlers.account_from_params(params)


@pytest.mark.usefixtures('patch_bad_db_connection')
def test_account_from_params_ServerError_bad_db(monkeypatch, mocker):
    """It returns Server Error if it can't connect to the database"""
    # FIXME: Should return HTTP 503 when we have that exception class
    params = {
        'api_key': '08e3918eeb8bf4469924f062072459a8',
        'from': 0,
        'page': 1,
        'page_size': 1
    }
    with pytest.raises(ServerError):
        v2_handlers.account_from_params(params)


# end account_from_params() tests


# items() tests ...


@pytest.mark.usefixtures('disable_auth')
def test_items_makes_es_request(monkeypatch):
    """multiple_items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = {'q': 'abcd', 'from': 0, 'page': 1, 'page_size': 1}
    v2_handlers.items(params)  # No error


@pytest.mark.usefixtures('disable_auth')
def test_items_Exception_for_elasticsearch_errs(monkeypatch):
    """An Elasticsearch error response other than a 400 results in a 500"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    # Simulate some unsuccessful status code from Elasticsearch, other than a
    # 400 Bad Request.  Say a 500 Server Error, or a 404.
    params = {'q': 'goodquery', 'from': 0, 'page': 1, 'page_size': 1}
    with pytest.raises(Exception):
        v2_handlers.items(params)


# multiple_items() tests ...


@pytest.mark.usefixtures('disable_auth')
def test_multiple_items_calls_items_correctly(monkeypatch):
    """/v2/items calls items() with dictionary"""
    def mock_items(arg):
        assert isinstance(arg, dict)
        return minimal_good_response
    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    client.get('/v2/items')


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
@pytest.mark.usefixtures('stub_tracking')
async def test_multiple_items_formats_response_metadata(monkeypatch, mocker):
    """multiple_items() assembles the correct response metadata"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    request_stub = mocker.stub()
    params = QueryParams({'q': 'abcd'})
    response_obj = await v2_handlers.multiple_items(params, request_stub)
    result = json.loads(response_obj.content)

    # See minimal_good_response above
    assert result['count'] == 1
    assert result['start'] == 1   # page 1; the default
    assert result['limit'] == 10  # the default
    assert result['docs'] == \
        [hit['_source'] for hit in minimal_good_response['hits']['hits']]


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_multiple_items_BadRequest_for_bad_param_value(monkeypatch,
                                                             mocker):
    """Input is validated and bad values for fields with constraints result in
    400 Bad Request responses"""
    params = QueryParams({'rights': "Not the URL it's supposed to be"})
    request_stub = mocker.stub()
    with pytest.raises(BadRequest):
        await v2_handlers.multiple_items(params, request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
async def test_multiple_items_BadRequest_for_unparseable_term(monkeypatch,
                                                              mocker):
    """User input that is unparseable by Elasticsearch results in a 400"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    # Elasticsearch can not parse the following query term and responds with
    # an HTTP 400 Bad Request.
    params = QueryParams({'sourceResource.title': 'this AND AND that'})
    request_stub = mocker.stub()
    with pytest.raises(BadRequest) as excinfo:
        await v2_handlers.multiple_items(params, request_stub)
    assert 'Invalid query' in str(excinfo)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_multiple_items_ServerError_for_misc_app_exception(monkeypatch,
                                                                 mocker):
    """A bug in our application that raises an Exception results in
    a ServerError (HTTP 500) with a generic message"""
    monkeypatch.setattr(
        search_query.SearchQuery, '__init__', mock_application_exception)
    params = QueryParams({'q': 'goodquery'})
    request_stub = mocker.stub()
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.multiple_items(params, request_stub)
    assert 'Unexpected error'in str(excinfo)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
async def test_multiple_items_handles_query_parameters(monkeypatch, mocker):
    """multiple_items() makes a good `goodparams' from querystring params"""
    def mock_searchquery(params_to_check):
        assert params_to_check == {'q': 'test'}
        return {}
    monkeypatch.setattr(search_query, 'SearchQuery', mock_searchquery)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    request_stub = mocker.stub()
    params = QueryParams({'q': 'test'})
    await v2_handlers.multiple_items(params, request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
async def test_multiple_items_reraises_Forbidden(monkeypatch, mocker):
    """It reraises a Forbidden that gets thrown in items()"""

    def mock_forbidden_items(*args):
        raise Forbidden()

    monkeypatch.setattr(v2_handlers, 'items', mock_forbidden_items)
    params = QueryParams({'q': 'test'})
    request_stub = mocker.stub()
    with pytest.raises(Forbidden):
        await v2_handlers.multiple_items(params, request_stub)


@pytest.mark.asyncio
async def test_multiple_items_calls_track_w_correct_params(monkeypatch,
                                                           mocker):
    """It calls dplaapi.analytics.track() correctly"""

    def mock_items(*argv):
        return minimal_good_response

    def mock_account(*argv):
        return models.Account(key='a1b2c3', email='x@example.org')

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    track_stub = mocker.stub(name='track_stub')
    monkeypatch.setattr(v2_handlers, 'track', track_stub)
    request_stub = mocker.stub(name='request_stub')
    params = QueryParams({'q': 'test'})
    ok_data = {
        'count': 1,
        'start': 1,
        'limit': 10,
        'docs': [{'sourceResource': {'title': 'x'}}],
        'facets': []
    }

    await v2_handlers.multiple_items(params, request_stub)
    track_stub.assert_called_once_with(request_stub, ok_data, 'a1b2c3',
                                       'Item search results')


# end multiple_items tests.

# specific_items tests ...


@pytest.mark.usefixtures('disable_api_key_check')
def test_specific_item_path(monkeypatch, mocker):
    """/v2/items/{id} calls items() with correct 'ids' parameter"""
    mocker.patch('dplaapi.handlers.v2.items')
    client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a')
    v2_handlers.items.assert_called_once_with(
        {'page': 1, 'page_size': 1, 'sort_order': 'asc',
         'ids': ['13283cd2bd45ef385aae962b144c7e6a']})


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_handles_multiple_ids(monkeypatch, mocker):
    """It splits ids on commas and calls items() with a list of those IDs"""
    def mock_items(arg):
        assert len(arg['ids']) == 2
        return minimal_good_response

    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867a39cac531e13a48c1'
    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    request_stub = mocker.stub()
    await v2_handlers.specific_item(ids, QueryParams({}), request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_ids_1(mocker):
    request_stub = mocker.stub()
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('x', QueryParams({}), request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_ids_2(mocker):
    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867'
    request_stub = mocker.stub()
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item(ids, QueryParams({}), request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_accepts_callback_querystring_param(monkeypatch,
                                                                mocker):

    def mock_items(arg):
        return minimal_good_response

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    request_stub = mocker.stub()
    await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                    QueryParams({'callback': 'f'}),
                                    request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_rejects_bad_querystring_param(mocker):
    request_stub = mocker.stub()
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                        QueryParams({'page_size': 1}),
                                        request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_BadRequest_for_ValidationError(monkeypatch,
                                                            mocker):

    def mock_items(arg):
        raise ValidationError('No!')

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    request_stub = mocker.stub()
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                        {},
                                        request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_auth')
async def test_specific_items_reraises_Forbidden(monkeypatch, mocker):
    """It reraises a Forbidden that gets thrown in items()"""

    def mock_forbidden_items(*args):
        raise Forbidden()

    monkeypatch.setattr(v2_handlers, 'items', mock_forbidden_items)
    request_stub = mocker.stub()
    with pytest.raises(Forbidden):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                        {},
                                        request_stub)


@pytest.mark.asyncio
@pytest.mark.usefixtures('disable_api_key_check')
async def test_specific_item_NotFound_for_zero_hits(monkeypatch, mocker):
    """It raises a NotFound if there are no documents"""

    def mock_zero_items(*args):
        return {'hits': {'total': 0}}

    monkeypatch.setattr(v2_handlers, 'items', mock_zero_items)
    request_stub = mocker.stub()
    with pytest.raises(NotFound):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                        {},
                                        request_stub)


@pytest.mark.asyncio
async def test_specific_item_calls_track_w_correct_params(monkeypatch,
                                                          mocker):
    """It calls dplaapi.analytics.track() correctly"""

    def mock_items(*argv):
        return minimal_good_response

    def mock_account(*argv):
        return models.Account(key='a1b2c3', email='x@example.org')

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    monkeypatch.setattr(v2_handlers, 'account_from_params', mock_account)
    track_stub = mocker.stub(name='track_stub')
    monkeypatch.setattr(v2_handlers, 'track', track_stub)
    request_stub = mocker.stub(name='request_stub')
    ok_data = {
        'count': 1,
        'docs': [{'sourceResource': {'title': 'x'}}]
    }

    await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                    {},
                                    request_stub)
    track_stub.assert_called_once_with(request_stub, ok_data, 'a1b2c3',
                                       'Fetch items')


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
    """It raises ServerError when the EMAIL_FROM env. var. is undefined"""
    monkeypatch.delenv('EMAIL_FROM', raising=False)
    with pytest.raises(ServerError):
        v2_handlers.send_email('x', 'testto@example.org')


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


def test_send_api_key_email_reraises_ServerError(monkeypatch):
    def naughty_send_email(*args):
        raise ServerError('No.')

    monkeypatch.setattr(v2_handlers, 'send_email', naughty_send_email)
    with pytest.raises(ServerError):
        v2_handlers.send_api_key_email('x@example.org', 'a1b2c3')


def test_send_api_key_email_raises_ServerError_for_Exception(monkeypatch):
    def buggy_send_email(*args):
        1/0

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(ServerError):
        v2_handlers.send_api_key_email('x@example.org', 'a1b2c3')


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


def test_send_reminder_email_reraises_ServerError(monkeypatch):
    def naughty_send_email(*args):
        raise ServerError('No.')

    monkeypatch.setattr(v2_handlers, 'send_email', naughty_send_email)
    with pytest.raises(ServerError):
        v2_handlers.send_reminder_email('x@example.org', 'a1b2c3')


def test_send_reminder_email_raises_ServerError_for_Exception(monkeypatch):
    def buggy_send_email(*args):
        1/0

    monkeypatch.setattr(v2_handlers, 'send_email', buggy_send_email)
    with pytest.raises(ServerError):
        v2_handlers.send_reminder_email('x@example.org', 'a1b2c3')


@pytest.mark.asyncio
async def test_api_key_flunks_bad_email():
    """api_key() rejects an obviously malformed email address"""
    # But only the most obvious cases involving misplaced '@' or lack of '.'
    bad_addrs = ['f@@ey', '56b7165e4f8a54b4faf1e04c46a6145c']
    for addr in bad_addrs:
        with pytest.raises(BadRequest):
            await v2_handlers.api_key(addr)


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
    with pytest.raises(ConflictError):
        await v2_handlers.api_key('x@example.org')
    stub.assert_called_once_with('x@example.org',
                                 '08e3918eeb8bf4469924f062072459a8')


@pytest.mark.asyncio
@pytest.mark.usefixtures('patch_bad_db_connection')
async def test_api_key_raises_ServerError_for_bad_db_connection(monkeypatch,
                                                                mocker):
    """api_key() raises ServerError if it can't connect to the database"""
    with pytest.raises(ServerError):
        await v2_handlers.api_key('x@example.org')


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
    await v2_handlers.api_key('x@example.org')

    models.Account.__init__.assert_called_with(
        mocker.ANY,
        key='08e3918eeb8bf4469924f062072459a8',
        email='x@example.org',
        enabled=True)


def test_api_key_options():
    """OPTIONS /api_key works as designed"""
    response = client.options('/v2/api_key')
    assert response.status_code == 200
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert response.headers['Access-Control-Allow-Methods'] == 'POST'


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
        'sourceResource.date.begin.decade': {
            '_type': 'date_histogram',
            'entries': [
                {
                    'time': '1520',
                    'count': 10
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
    headers = {k: v for k, v in rv.headers}
    assert headers['content-type'] == 'application/javascript'
    assert rv.content == b'f({})'


# Exception-handling and HTTP status double-checks


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_500_means_client_500(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_elasticsearch_503_means_client_503(monkeypatch):
    # TODO: need to revise dplaapi.handlers.v2.items() and add a
    # ServiceUnavailable exception class
    pass


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_400_means_client_400(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    response = client.get('/v2/items?q=some+bad+search')
    assert response.status_code == 400
    assert response.json() == 'Invalid query'


@pytest.mark.usefixtures('disable_auth')
def test_elasticsearch_404_means_client_500(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_404)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


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

    monkeypatch.setattr(search_query.SearchQuery, '__init__', problem_func)
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

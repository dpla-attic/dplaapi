
"""Test dplaapi.handlers.v2"""

import pytest
import requests
import json
from apistar import test
from apistar.exceptions import BadRequest, ValidationError
from apistar.http import QueryParams, Response, JSONResponse
from dplaapi import app
from dplaapi import search_query, types
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


# items() tests ...


def test_items_makes_es_request(monkeypatch):
    """multiple_items() makes an HTTP request to Elasticsearch"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = {'q': 'abcd', 'from': 0, 'page': 1, 'page_size': 1}
    v2_handlers.items(params)  # No error


def test_items_Exception_for_elasticsearch_errs(monkeypatch):
    """An Elasticsearch error response other than a 400 results in a 500"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    # Simulate some unsuccessful status code from Elasticsearch, other than a
    # 400 Bad Request.  Say a 500 Server Error, or a 404.
    params = {'q': 'goodquery', 'from': 0, 'page': 1, 'page_size': 1}
    with pytest.raises(Exception):
        v2_handlers.items(params)


# multiple_items() tests ...

def test_multiple_items_calls_items_correctly(monkeypatch):
    """/v2/items calls items() with dictionary"""
    def mock_items(arg):
        assert isinstance(arg, dict)
        return minimal_good_response
    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    client.get('/v2/items')


@pytest.mark.asyncio
async def test_multiple_items_formats_response_metadata(monkeypatch):
    """multiple_items() assembles the correct response metadata"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = QueryParams({'q': 'abcd'})
    response_obj = await v2_handlers.multiple_items(params)
    result = json.loads(response_obj.content)

    # See minimal_good_response above
    assert result['count'] == 1
    assert result['start'] == 1   # page 1; the default
    assert result['limit'] == 10  # the default
    assert result['docs'] == \
        [hit['_source'] for hit in minimal_good_response['hits']['hits']]


@pytest.mark.asyncio
async def test_multiple_items_BadRequest_for_bad_param_value():
    """Input is validated and bad values for fields with constraints result in
    400 Bad Request responses"""
    params = QueryParams({'rights': "Not the URL it's supposed to be"})
    with pytest.raises(BadRequest):
        await v2_handlers.multiple_items(params)


@pytest.mark.asyncio
async def test_multiple_items_BadRequest_for_unparseable_term(monkeypatch):
    """User input that is unparseable by Elasticsearch results in a 400"""
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    # Elasticsearch can not parse the following query term and responds with
    # an HTTP 400 Bad Request.
    params = QueryParams({'sourceResource.title': 'this AND AND that'})
    with pytest.raises(BadRequest) as excinfo:
        await v2_handlers.multiple_items(params)
    assert 'Invalid query' in str(excinfo)


@pytest.mark.asyncio
async def test_multiple_items_ServerError_for_misc_app_exception(monkeypatch):
    """A bug in our application that raises an Exception results in
    a ServerError (HTTP 500) with a generic message"""
    monkeypatch.setattr(
        search_query.SearchQuery, '__init__', mock_application_exception)
    params = QueryParams({'q': 'goodquery'})
    with pytest.raises(ServerError) as excinfo:
        await v2_handlers.multiple_items(params)
    assert 'Unexpected error'in str(excinfo)


@pytest.mark.asyncio
async def test_multiple_items_handles_query_parameters(monkeypatch):
    """items() makes a good `goodparams' dict from querystring params"""
    def mock_searchquery(params_to_check):
        assert params_to_check == {'q': 'test'}
        return {}
    monkeypatch.setattr(search_query, 'SearchQuery', mock_searchquery)
    monkeypatch.setattr(requests, 'post', mock_es_post_response_200)
    params = QueryParams({'q': 'test'})
    await v2_handlers.multiple_items(params)


# end multiple_items tests.

# specific_items tests ...


def test_specific_item_path(mocker):
    """/v2/items/{id} calls items() with correct 'ids' parameter"""
    mocker.patch('dplaapi.handlers.v2.items')
    client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a')
    v2_handlers.items.assert_called_once_with(
        {'page': 1, 'page_size': 1, 'sort_order': 'asc',
         'ids': ['13283cd2bd45ef385aae962b144c7e6a']})


@pytest.mark.asyncio
async def test_specific_item_handles_multiple_ids(monkeypatch):
    """It splits ids on commas and calls items() with a list of those IDs"""
    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867a39cac531e13a48c1'

    def mock_items(arg):
        assert len(arg['ids']) == 2
        return minimal_good_response

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    await v2_handlers.specific_item(ids, QueryParams({}))


@pytest.mark.asyncio
async def test_specific_item_rejects_bad_ids_1():
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('x', QueryParams({}))


@pytest.mark.asyncio
async def test_specific_item_rejects_bad_ids_2():
    ids = '13283cd2bd45ef385aae962b144c7e6a,00000062461c867'
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item(ids, QueryParams({}))


@pytest.mark.asyncio
async def test_specific_item_accepts_callback_querystring_param(monkeypatch):

    def mock_items(arg):
        return minimal_good_response

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                    QueryParams({'callback': 'f'}))


@pytest.mark.asyncio
async def test_specific_item_rejects_bad_querystring_param():
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a',
                                        QueryParams({'page_size': 1}))


@pytest.mark.asyncio
async def test_specific_item_BadRequest_for_ValidationError(monkeypatch):

    def mock_items(arg):
        raise ValidationError('No!')

    monkeypatch.setattr(v2_handlers, 'items', mock_items)
    with pytest.raises(BadRequest):
        await v2_handlers.specific_item('13283cd2bd45ef385aae962b144c7e6a', {})

# end specific_items tests.


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


def test_elasticsearch_500_means_client_500(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_err)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_elasticsearch_503_means_client_503(monkeypatch):
    # TODO: need to revise dplaapi.handlers.v2.items() and add a
    # ServiceUnavailable exception class
    pass


def test_elasticsearch_400_means_client_400(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_400)
    response = client.get('/v2/items?q=some+bad+search')
    assert response.status_code == 400
    assert response.json() == 'Invalid query'


def test_elasticsearch_404_means_client_500(monkeypatch):
    monkeypatch.setattr(requests, 'post', mock_es_post_response_404)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_ItemsQueryType_ValidationError_means_client_400(monkeypatch):

    def badinit(*args, **kwargs):
        raise ValidationError('no good')

    monkeypatch.setattr(types.ItemsQueryType, '__init__', badinit)
    response = client.get('/v2/items?hasView.format=some+bad+string')
    assert response.status_code == 400


def test_ItemsQueryType_Exception_means_client_500(monkeypatch):

    def badinit(*args, **kwargs):
        raise AttributeError()

    monkeypatch.setattr(types.ItemsQueryType, '__init__', badinit)
    response = client.get('/v2/items?provider.name=a+provider')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_search_query_Exception_means_client_500(monkeypatch):
    # have q_fields_clause_items raise KeyError

    def problem_func(*args, **kwargs):
        raise KeyError()

    monkeypatch.setattr(search_query, 'q_fields_clause', problem_func)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.json() == 'Unexpected error'


def test_compact_with_field_param():
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
    result = v2_handlers.compact(before, {'fields': 'sourceResource.date'})
    assert result == after


def test_compact_without_field_param():
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
    result = v2_handlers.compact(before, {'fields': 'sourceResource.date'})
    assert result == before

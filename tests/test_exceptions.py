import os
import pytest
from dplaapi import app
import dplaapi.handlers.v2 as v2_handlers
from dplaapi.types import ItemsQueryType
from apistar.exceptions import ValidationError
from starlette.testclient import TestClient


client = TestClient(app,
                    base_url='http://localhost',
                    raise_server_exceptions=False)


ok_content_type = 'application/json; charset=utf-8'


def mock_application_bug(*args, **kwargs):
    return {'impossible': 1/0}


def mock_validation_failure(*args, **kwargs):
    raise ValidationError('x is not a valid parameter')


def mock_search_items_w_no_results(*args, **kwargs):
    return {'hits': {'total': {'value': 0}}}

def mock_search_necro_w_no_results(*args, **kwargs):
    return {'hits': {'total': {'value': 0}}}


@pytest.fixture(scope='function')
def disable_auth():
    os.environ['DISABLE_AUTH'] = 'true'
    yield
    del(os.environ['DISABLE_AUTH'])


@pytest.mark.usefixtures('disable_auth')
def test_unexpected_errors_are_handled_correctly(monkeypatch):
    monkeypatch.setattr(v2_handlers, 'search_items', mock_application_bug)
    response = client.get('/v2/items')
    assert response.status_code == 500
    assert response.headers['content-type'] == ok_content_type
    assert response.json() == 'Unexpected error'


@pytest.mark.usefixtures('disable_auth')
def test_validation_errors_are_handled_correctly(monkeypatch):
    monkeypatch.setattr(ItemsQueryType, '__init__', mock_validation_failure)
    response = client.get('/v2/items?x=y')
    assert response.status_code == 400
    assert response.headers['content-type'] == ok_content_type
    assert response.json() == 'x is not a valid parameter'


@pytest.mark.usefixtures('disable_auth')
def test_thrown_http_errors_are_handled_correctly(monkeypatch):
    monkeypatch.setattr(v2_handlers, 'search_items',
                        mock_search_items_w_no_results)
    monkeypatch.setattr(v2_handlers, 'search_necro',
                        mock_search_necro_w_no_results)
    response = client.get('/v2/items/13283cd2bd45ef385aae962b144c7e6a')
    assert response.status_code == 404
    assert response.headers['content-type'] == ok_content_type
    assert response.json() == 'Not Found'

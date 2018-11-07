
from starlette.testclient import TestClient
from dplaapi import app


client = TestClient(app,
                    base_url='http://localhost',
                    raise_server_exceptions=False)


def test_root_redirect():
    response = client.get('/', allow_redirects=False)
    assert response.status_code == 301
    assert response.headers['Location'] == '/v2/items'


from apistar import test
from dplaapi import app


client = test.TestClient(app, hostname='localhost')


def test_root_redirect():
    response = client.get('/', allow_redirects=False)
    assert response.status_code == 301
    assert response.headers['Location'] == '/v2/items'

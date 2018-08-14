
import os
from apistar import test

os.environ['ES_BASE'] = 'x'
from dplaapi import app                 # noqa: E402


client = test.TestClient(app)


def test_schema():
    response = client.get('/schema/')
    assert response.status_code == 200
    data = response.json()
    assert 'paths' in data

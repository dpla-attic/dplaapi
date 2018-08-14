
import os
os.environ['ES_BASE'] = 'x'

from apistar import test
from dplaapi import app


client = test.TestClient(app)


def test_schema():
    response = client.get('/schema/')
    assert response.status_code == 200
    data = response.json()
    assert 'paths' in data

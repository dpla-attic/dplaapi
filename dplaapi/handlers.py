
import logging
import requests
import apistar
from urllib.parse import quote_plus

import dplaapi
from . import validators
from .exceptions import ServerError


log = logging.getLogger(__name__)


async def index(request: apistar.http.Request) -> dict:
    """Redirect to API schema"""
    headers = {'Location': '/schema/'}
    data = headers
    return apistar.http.JSONResponse(data, status_code=301, headers=headers)

async def request_info(request: apistar.http.Request) -> dict:
    """Get information about the request"""
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    }

async def search(term: str, fail: bool = False) -> dict:
    """Get a search result"""
    try:
        s = validators.Search(term=term)
        url = "%s/_search?q=%s" % (dplaapi.ES_BASE, quote_plus(s.term))
        if fail:
            url = "%s/nosuchthing/_bad" % dplaapi.ES_BASE
        resp = requests.get(url)
        resp.raise_for_status()
        result = resp.json()
        return {'hits': result['hits']}
    except apistar.exceptions.ValidationError as e:
        raise apistar.exceptions.BadRequest(e.detail)
    except requests.exceptions.RequestException as e:
        log.exception('Error querying Elasticsearch')
        raise ServerError(
            {'message': 'Backend search operation failed'})
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError({'message': 'Unexpected error'})

async def bad_get_path() -> dict:
    raise apistar.exceptions.NotFound({'message': 'Not Found'})


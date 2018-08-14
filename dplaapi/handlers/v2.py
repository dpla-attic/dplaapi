
import apistar
import logging
import requests
from urllib.parse import quote_plus

import dplaapi
from dplaapi import validators
from dplaapi.exceptions import ServerError


log = logging.getLogger(__name__)


async def items(q: str) -> dict:
    """Get "item" records"""
    try:
        s = validators.Search(term=q)
        url = "%s/_search?q=%s" % (dplaapi.ES_BASE, quote_plus(s.term))
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

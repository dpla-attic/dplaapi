
import apistar
import logging
import requests
from urllib.parse import quote_plus

import dplaapi
from dplaapi.exceptions import ServerError


log = logging.getLogger(__name__)


class ItemsType(apistar.types.Type):
    """Parameter constraints for item searches"""
    q = apistar.validators.String(
        title='Search term',
        description='Search term',
        min_length=4,
        max_length=200,
        allow_null=False)


async def items(q: str) -> dict:
    """Get "item" records"""
    try:
        params = ItemsType(q=q)
        url = "%s/_search?q=%s" % (dplaapi.ES_BASE, quote_plus(params.q))
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

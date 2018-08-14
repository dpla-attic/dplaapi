
import apistar
import logging
import requests
from urllib.parse import quote_plus

import dplaapi
from dplaapi.exceptions import ServerError


log = logging.getLogger(__name__)


class ItemsQueryType(apistar.types.Type):
    """Parameter constraints for item searches"""
    q = apistar.validators.String(
        title='Search term',
        description='Search term',
        min_length=4,
        max_length=200,
        allow_null=True)

    def is_match_all(self):
        return not self.q


async def items(q: str) -> dict:
    """Get "item" records"""
    try:
        params = ItemsQueryType(q=q)
        url = "%s/_search?q=%s" % (dplaapi.ES_BASE, quote_plus(params.q))
        resp = requests.get(url)
        resp.raise_for_status()
        result = resp.json()
        return {'hits': result['hits']}
    except apistar.exceptions.ValidationError as e:
        raise apistar.exceptions.BadRequest(e.detail)
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 400:
            # Assume that a Bad Request is the user's fault and we're getting
            # this because the query doesn't parse due to a bad search term
            # parameter.  For example "this AND AND that".
            raise apistar.exceptions.BadRequest('Invalid query')
        else:
            log.exception('Error querying Elasticsearch')
            raise ServerError('Backend search operation failed')
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')

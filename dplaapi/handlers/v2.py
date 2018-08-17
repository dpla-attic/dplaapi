
import apistar
import logging
import requests
import dplaapi
from dplaapi.types import ItemsQueryType
import dplaapi.search_query
from dplaapi.exceptions import ServerError
from dplaapi.search_query import SearchQuery

log = logging.getLogger(__name__)


def items(id_or_queryparams) -> dict:
    """Get "item" records"""
    try:
        if isinstance(id_or_queryparams, str):
            goodparams = ItemsQueryType({'id': id_or_queryparams})
        else:
            goodparams = ItemsQueryType({k: v for [k, v] in id_or_queryparams})
        sq = SearchQuery(goodparams)
        log.debug("Elasticsearch QUERY (Python dict):\n%s" % sq.query)
        resp = requests.post("%s/_search" % dplaapi.ES_BASE, json=sq.query)
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


async def multiple_items(params: apistar.http.QueryParams) -> dict:
    return items(params)


async def single_item(record_id: str) -> dict:
    return items(record_id)

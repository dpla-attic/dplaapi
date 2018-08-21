
import apistar
import logging
import requests
import dplaapi
import time
import re
from dplaapi.types import ItemsQueryType
import dplaapi.search_query
from dplaapi.exceptions import ServerError
from dplaapi.search_query import SearchQuery
from dplaapi.facets import facets


log = logging.getLogger(__name__)


def items(ids_or_queryparams):
    """Get "item" records"""
    try:
        if isinstance(ids_or_queryparams, list):
            goodparams = {'ids': ids_or_queryparams}
        else:
            goodparams = ItemsQueryType({k: v for [k, v]
                                         in ids_or_queryparams})
        sq = SearchQuery(goodparams)
        log.debug("Elasticsearch QUERY (Python dict):\n%s" % sq.query)
        resp = requests.post("%s/_search" % dplaapi.ES_BASE, json=sq.query)
        resp.raise_for_status()
        result = resp.json()
        return (result, goodparams)
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


def formatted_facets(es6_facets):
    """Return list of facets that comply with our legacy format

    The v2 API is legacy, and the DPLA API specification is for facets to look
    the way they used to, coming out of Elasticsearch 0.90.

    Arguments
    - es6_facets: dict of 'aggregations' from Elasticsearch
    """
    func = {
        'terms': term_facets,
        'date_histogram': date_facets,
        'geo_distance': geo_facets
    }
    # facets[k][1] is the 2nd element of the tuple that gives the type of
    # facet. See `facets.facets'.
    return {k: func[facets[k][1]](v) for k, v in es6_facets.items()}


def geo_facets(dict_with_buckets):
    ranges = [{'from': b['from'], 'to': b['to'], 'count': b['doc_count']}
              for b in dict_with_buckets['buckets']]
    return {'_type': 'geo_distance', 'ranges': ranges}


def date_facets(dict_with_buckets):
    entries = [{'time': date_formatted(b['key']), 'count': b['doc_count']}
               for b in dict_with_buckets['buckets']]
    return {'_type': 'date_histogram', 'entries': entries}


def date_formatted(es6_time_value):
    seconds_since_epoch = es6_time_value / 1000
    return time.strftime('%Y-%m-%d', time.gmtime(seconds_since_epoch))


def term_facets(dict_with_buckets):
    terms = [{'term': b['key'], 'count': b['doc_count']}
             for b in dict_with_buckets['buckets']]
    return {'_type': 'terms', 'terms': terms}


async def multiple_items(params: apistar.http.QueryParams) -> dict:
    (result, goodparams) = items(params)
    return {
        'count': result['hits']['total'],
        'start': (int(goodparams['page']) - 1)
                  * int(goodparams['page_size'])               # noqa: E131
                  + 1,                                         # noqa: E131
        'limit': int(goodparams['page_size']),
        'docs': [hit['_source'] for hit in result['hits']['hits']],
        'facets': formatted_facets(result.get('aggregations', {}))
    }


async def specific_item(id_or_ids: str) -> dict:
    ids = id_or_ids.split(',')
    for the_id in ids:
        if not re.match(r'[a-f0-9]{32}$', the_id):
            raise apistar.exceptions.BadRequest("Bad ID: %s" % the_id)
    (result, notused) = items(ids)
    del(notused)
    return {
        'count': result['hits']['total'],
        'docs': [hit['_source'] for hit in result['hits']['hits']]
    }

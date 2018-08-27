
from apistar import exceptions, http
import logging
import requests
import dplaapi
import re
import json
from dplaapi.types import ItemsQueryType
import dplaapi.search_query
from dplaapi.exceptions import ServerError
from dplaapi.search_query import SearchQuery
from dplaapi.facets import facets


log = logging.getLogger(__name__)


def items(params):
    """Get "item" records

    Arguments:
    - params: Dict of querystring or path parameters
    """
    sq = SearchQuery(params)
    log.debug("Elasticsearch QUERY (Python dict):\n%s" % sq.query)
    try:
        resp = requests.post("%s/_search" % dplaapi.ES_BASE, json=sq.query)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        if resp.status_code == 400:
            # Assume that a Bad Request is the user's fault and we're getting
            # this because the query doesn't parse due to a bad search term
            # parameter.  For example "this AND AND that".
            raise exceptions.BadRequest('Invalid query')
        else:
            log.exception('Error querying Elasticsearch')
            raise Exception('Backend search operation failed')
    result = resp.json()
    return result


def formatted_facets(es6_aggregations):
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
    return {k: func[facets[k][1]](v) for k, v in es6_aggregations.items()}


def geo_facets(this_agg):
    ranges = [{'from': b['from'], 'to': b['to'], 'count': b['doc_count']}
              for b in this_agg['buckets']]
    return {'_type': 'geo_distance', 'ranges': ranges}


def date_facets(this_agg):
    entries = [{'time': bucket_date(b), 'count': b['doc_count']}
               for b in dict_with_date_buckets(this_agg)]
    return {'_type': 'date_histogram', 'entries': entries}


def dict_with_date_buckets(a_dict):
    """Given an Elasticsearch aggregation, return the 'buckets' part.

    Also sort it in descending order if it's a range facet (decade, century)
    because Elasticsearch always returns those in ascending order.
    """
    if 'buckets' in a_dict:
        buckets = a_dict['buckets']
        buckets.sort(key=lambda x: -x['from'])
        return buckets
    else:
        for k, v in a_dict.items():
            if isinstance(v, dict) and 'buckets' in v:
                return a_dict[k]['buckets']
    raise Exception('Should not happen: aggregations dict from Elasticsearch '
                    'does not have an aggregation with "buckets" array')


def bucket_date(a_dict):
    if 'from_as_string' in a_dict:
        return a_dict['from_as_string']
    else:
        return a_dict['key_as_string']


def term_facets(this_agg):
    terms = [{'term': b['key'], 'count': b['doc_count']}
             for b in this_agg['buckets']]
    return {'_type': 'terms', 'terms': terms}


def response_object(data, params):
    if 'callback' in params:
        headers = {'Content-Type': 'application/javascript'}
        content = "%s(%s)" % (params['callback'], json.dumps(data))
        return http.Response(content=content, headers=headers)
    else:
        return http.JSONResponse(data)


async def multiple_items(
            params: http.QueryParams) -> http.JSONResponse:
    try:
        goodparams = ItemsQueryType({k: v for [k, v] in params})
        result = items(goodparams)
        rv = {
            'count': result['hits']['total'],
            'start': (int(goodparams['page']) - 1)
                      * int(goodparams['page_size'])               # noqa: E131
                      + 1,                                         # noqa: E131
            'limit': int(goodparams['page_size']),
            'docs': [hit['_source'] for hit in result['hits']['hits']],
            'facets': formatted_facets(result.get('aggregations', {}))
        }
        return response_object(rv, goodparams)

    except exceptions.BadRequest:
        raise
    except exceptions.ValidationError as e:
        raise exceptions.BadRequest(e.detail)
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')


async def specific_item(id_or_ids: str,
                        params: http.QueryParams) -> dict:
    try:
        for k in list(params):        # list of tuples
            if k[0] != 'callback' and k[0] != 'api_key':
                raise exceptions.BadRequest('Unrecognized parameter %s' % k[0])
        goodparams = ItemsQueryType({k: v for [k, v] in params})
        ids = id_or_ids.split(',')
        for the_id in ids:
            if not re.match(r'[a-f0-9]{32}$', the_id):
                raise exceptions.BadRequest("Bad ID: %s" % the_id)
        goodparams.update({'ids': ids})
        goodparams['page_size'] = len(ids)
        result = items(goodparams)
        rv = {
            'count': result['hits']['total'],
            'docs': [hit['_source'] for hit in result['hits']['hits']]
        }
        return response_object(rv, goodparams)
    except exceptions.BadRequest:
        raise
    except exceptions.ValidationError as e:
        raise exceptions.BadRequest(e.detail)
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')

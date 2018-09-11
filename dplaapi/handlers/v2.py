
from apistar import exceptions, http
import logging
import requests
import dplaapi
import re
import json
import os
import boto3
import secrets
from cachetools import cached, TTLCache
from dplaapi.types import ItemsQueryType
import dplaapi.search_query
from dplaapi.exceptions import ServerError, ConflictError
from dplaapi.search_query import SearchQuery
from dplaapi.facets import facets
from dplaapi.models import db, Account
from dplaapi.analytics import track
from peewee import OperationalError, DoesNotExist

log = logging.getLogger(__name__)
ok_email_pat = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
cache = TTLCache(maxsize=100, ttl=20)


def items_key(params):
    """Return a hashable object (a tuple) suitable for a cache key

    A dict is not hashable, so we need something hashable for caching the
    items() function.
    """

    def hashable(thing):
        if isinstance(thing, list):
            return ','.join(sorted(thing))
        else:
            return thing

    # A tuple of dict items() plus a token to prevent collisions with
    # keys from other functions that might use the same cache
    items = [(k, hashable(v)) for (k, v) in params.items()]
    return tuple(sorted(items)) + ('v2_items',)


@cached(cache, key=items_key)
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
    """Return dict of facets that comply with our legacy format, or []

    The v2 API is legacy, and the DPLA API specification is for facets to look
    the way they used to, coming out of Elasticsearch 0.90.

    And yes, it's a dict if it's filled-in, and a List if it is empty. That's
    the way the legacy API has worked.

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
    rv = {k: func[facets[k][1]](v) for k, v in es6_aggregations.items()}
    if rv:
        return rv
    else:
        # Yes, an empty list, not a dict.
        return []


def geo_facets(this_agg):
    ranges = [{'from': b.get('from'), 'to': b.get('to'),
               'count': b['doc_count']}
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


def traverse_doc(path, doc):
    """Given a _source ES doc, parse a dotted-notation path value and return
    the part of the doc that it represents.

    Called by compact().  See tests/handlers/test_v2.py for examples.
    """
    leftpart = path.partition('.')[0]
    rightpart = path.partition('.')[2]
    if rightpart == '':
        return doc[leftpart]
    else:
        try:
            return traverse_doc(rightpart, doc[leftpart])
        except KeyError:
            # Some docs in a result may not have the given field
            return None


def compact(doc, params):
    """Display Elasticsearch 6 nested objects as they appeared in ES 0.90"""
    if 'fields' in params:
        rv = {}
        fieldlist = params['fields'].split(',')
        for field in fieldlist:
            val = traverse_doc(field, doc)
            if val:
                rv[field] = val
    else:
        rv = doc
    return rv


def response_headers(content_type):
    return {
        'Content-Type': content_type,
        'Access-Control-Allow-Origin': '*'
    }


def response_object(data, params):
    if 'callback' in params:
        headers = response_headers('application/javascript')
        content = "%s(%s)" % (params['callback'], json.dumps(data))
        return http.Response(content=content, headers=headers)
    else:
        headers = response_headers('application/json; charset=utf-8')
        return http.JSONResponse(data, headers=headers)


def send_email(message, destination):
    """Send email to the given destination, with the given message"""

    source = os.getenv('EMAIL_FROM')
    if not source:
        log.exception('EMAIL_FROM is undefined in environment')
        raise ServerError('Can not send email')
    destination = {'ToAddresses': [destination]}
    client = boto3.client('ses')
    client.send_email(
        Source=source, Destination=destination, Message=message)


def send_api_key_email(email, api_key):
    message = {
        'Body': {
            'Text': {
                'Data': 'Your API key is %s' % api_key
            }
        },
        'Subject': {'Data': 'Your new DPLA API key'}
    }
    try:
        send_email(message, email)
    except ServerError:
        raise
    except Exception:
        log.exception('Unexpected error')
        raise ServerError('Could not send API key to %s' % email)


def send_reminder_email(email, api_key):
    message = {
        'Body': {
            'Text': {
                'Data': 'The most recent API key for %s '
                        'is %s' % (email, api_key)
            }
        },
        'Subject': {'Data': 'Your existing DPLA API key'}
    }
    try:
        send_email(message, email)
    except ServerError:
        raise
    except Exception:
        log.exception('Unexpected error')
        raise ServerError('Could not send API key reminder email '
                          '(Tried to because there is already an api_key for '
                          'that email)')


def account_from_params(params):
    """Return an account for the API key extracted from the given parameters

    Return the Account or None if authentication is disabled.
    """
    if not os.getenv('DISABLE_AUTH'):
        account = None
        try:
            db.connect()
            account = Account.get(Account.key == params.get('api_key', ''))
        except (OperationalError, ValueError):
            # OperationalError indicates a problem connecting, such as when
            # the database is unavailable.
            # ValueError indicates that the configured Peewee maximum
            # connections have been exceeded.
            # TODO: should be HTTP 503
            log.exception('Failed to connect to database')
            raise ServerError('Backend API key account lookup failed')
        except DoesNotExist:
            # Do not assign account ...
            pass
        finally:
            db.close()

        if not account or not account.enabled:
            raise exceptions.Forbidden('Invalid or inactive API key')

        return account

    return None


async def multiple_items(params: http.QueryParams,
                         request: http.Request) -> http.JSONResponse:

    account = account_from_params(params)

    try:
        goodparams = ItemsQueryType({k: v for [k, v] in params})

        result = items(goodparams)
        log.debug('cache size: %d' % cache.currsize)
        rv = {
            'count': result['hits']['total'],
            'start': (int(goodparams['page']) - 1)
                      * int(goodparams['page_size'])               # noqa: E131
                      + 1,                                         # noqa: E131
            'limit': int(goodparams['page_size']),
            'docs': [compact(hit['_source'], goodparams)
                     for hit in result['hits']['hits']],
            'facets': formatted_facets(result.get('aggregations', {}))
        }

        if account and not account.staff:
            track(request, rv, account.key, 'Item search results')

        return response_object(rv, goodparams)

    except (exceptions.BadRequest, exceptions.Forbidden):
        raise
    except exceptions.ValidationError as e:
        raise exceptions.BadRequest(e.detail)
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')


async def specific_item(id_or_ids: str,
                        params: http.QueryParams,
                        request: http.Request) -> dict:

    account = account_from_params(params)

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
        log.debug('cache size: %d' % cache.currsize)

        if result['hits']['total'] == 0:
            raise exceptions.NotFound()

        rv = {
            'count': result['hits']['total'],
            'docs': [hit['_source'] for hit in result['hits']['hits']]
        }

        if account and not account.staff:
            track(request, rv, account.key, 'Fetch items')

        return response_object(rv, goodparams)

    except (exceptions.BadRequest, exceptions.Forbidden, exceptions.NotFound):
        raise
    except exceptions.ValidationError as e:
        raise exceptions.BadRequest(e.detail)
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')


async def api_key(email: str) -> dict:
    """Create a new API key"""

    if not re.match(ok_email_pat, email):
        raise exceptions.BadRequest('Bad email address')

    try:
        db.connect()
    except (OperationalError, ValueError):
        db.close()  # Must do this to release it to the connection pool
        log.exception('Failed to connect to database')
        raise ServerError('Can not create API key')

    try:
        old_acct = Account.get(
            Account.email == email, Account.enabled == True)  # noqa: E712
        send_reminder_email(email, old_acct.key)
        db.close()
        raise ConflictError(
            'There is already an API key for %s.  We have sent a reminder '
            'message to that address.' % email)
    except DoesNotExist:
        # We want for it not to exist yet.
        # Keep the database connection open.
        pass

    new_key = secrets.token_hex(16)
    try:
        with db.atomic():
            Account(key=new_key, email=email, enabled=True).save()
            send_api_key_email(email, new_key)
    finally:
        db.close()

    return {'message': 'API key created and sent to %s' % email}


async def api_key_options() -> http.Response:
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST'
    }
    return http.Response(content='', headers=headers)

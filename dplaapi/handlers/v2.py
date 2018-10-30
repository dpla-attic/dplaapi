
import logging
import requests
import dplaapi
import re
import json
import os
import boto3
import secrets
from starlette.exceptions import HTTPException
from starlette.background import BackgroundTask
from cachetools import cached, TTLCache
from dplaapi.types import ItemsQueryType, MLTQueryType, SuggestionQueryType
from dplaapi.exceptions import ServerError, ConflictError
from dplaapi.queries.search_query import SearchQuery
from dplaapi.queries.mlt_query import MLTQuery
from dplaapi.queries.suggestion_query import SuggestionQuery
from dplaapi.facets import facets
from dplaapi.models import db, Account
from dplaapi.analytics import track
from dplaapi.responses import JSONResponse, JavascriptResponse
from peewee import OperationalError, DoesNotExist

log = logging.getLogger(__name__)
ok_email_pat = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
search_cache = TTLCache(maxsize=100, ttl=20)
mlt_cache = TTLCache(maxsize=50, ttl=20)


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


def items(query):
    """Return "item" records from a search query

    The search query could either be a typical SearchQuery or a MLTQuery
    ("More Like This" query)

    Arguments:
    - query:  instance of SearchQuery or MLTQuery, which has a `query'
              property.
    """
    try:
        resp = requests.post("%s/_search" % dplaapi.ES_BASE, json=query.query)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        if resp.status_code == 400:
            # Assume that a Bad Request is the user's fault and we're getting
            # this because the query doesn't parse due to a bad search term
            # parameter.  For example "this AND AND that".
            raise HTTPException(400, 'Invalid query')
        else:
            log.exception('Error querying Elasticsearch')
            raise HTTPException(503, 'Backend search operation failed')
    result = resp.json()
    return result


@cached(search_cache, key=items_key)
def search_items(params):
    """Get "item" records

    Arguments:
    - params: Dict of querystring or path parameters
    """
    sq = SearchQuery(params)
    log.debug("Elasticsearch QUERY (Python dict):\n%s" % sq.query)
    return items(sq)


@cached(mlt_cache, key=items_key)
def mlt_items(params):
    """Get more-like-this "item" records

    Arguments:
    - params: Dict of querystring or path parameters
    """
    mltq = MLTQuery(params)
    log.debug("Elasticsearch QUERY (Python dict):\n%s" % mltq.query)
    return items(mltq)


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


def flatten(the_list):
    """Responsibly flatten a list of lists into a one-dimensional list

    Do not explode string values into lists!
    (Solutions on the web using itertools.chain() and [x for y in z for x in y]
    don't work because they explode strings into arrays.
    """
    if the_list is None:
        raise StopIteration
    for el in the_list:
        if isinstance(el, list):
            for sub_el in flatten(el):
                yield sub_el
        else:
            yield el


def traverse_doc(path, doc):
    """Given a _source ES doc, parse a dotted-notation path value and return
    the part of the doc that it represents.

    Called by compact().  See tests/handlers/test_v2.py for examples.

    Care must be taken to handle values that may be strings, objects, or lists.
    The tests illustrate how this handles the variations that we have in our
    data.
    """
    leftpart = path.partition('.')[0]
    rightpart = path.partition('.')[2]
    results = None
    if rightpart == '':
        # End of the line, so to speak, so return that value that we were
        # after.
        try:
            if isinstance(doc, dict):
                results = doc[leftpart]
            elif isinstance(doc, list):
                results = [traverse_doc(leftpart, el) for el in doc]
        except KeyError:
            # Some docs in a result may not have the given field
            pass
    else:
        # We're still in-progress traversing the path ...
        try:
            if isinstance(doc, dict):
                results = traverse_doc(rightpart, doc[leftpart])
            elif isinstance(doc, list):
                results = [traverse_doc(rightpart, el[leftpart]) for el in doc]
        except KeyError:
            # as above
            pass
    if isinstance(results, list):
        # Sure, it's a list, but it could be a list of lists if we've
        # encountered an object with a property that's list of objects, etc.,
        # so we have to use flatten() ...
        x = [el for el in flatten(results)]
        if not x:
            # empty list
            return None
        elif len(x) == 1:
            # for consistency, say that ['value'] is 'value'.
            return x[0]
        else:
            return x
    else:
        return results


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


def response_object(data, params, task=None):
    if 'callback' in params:
        content = "%s(%s)" % (params['callback'], json.dumps(data))
        return JavascriptResponse(content, background=task)
    else:
        return JSONResponse(data, background=task)


def send_email(message, destination):
    """Send email to the given destination, with the given message"""

    source = os.getenv('EMAIL_FROM')
    if not source:
        log.exception('EMAIL_FROM is undefined in environment')
        raise HTTPException(500, 'Can not send email')
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
    except HTTPException:
        raise
    except Exception:
        log.exception('Unexpected error')
        raise HTTPException(500, 'Could not send API key to %s' % email)


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
    except HTTPException:
        raise
    except Exception:
        log.exception('Unexpected error')
        raise HTTPException(500, 'Could not send API key reminder email '
                                 '(Tried to because there is already an '
                                 'api_key for that email)')


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
            log.exception('Failed to connect to database')
            raise HTTPException(503, 'Backend API key account lookup failed')
        except DoesNotExist:
            # Do not assign account ...
            pass
        finally:
            db.close()

        if not account or not account.enabled:
            raise HTTPException(403, 'Invalid or inactive API key')

        return account

    return None


async def multiple_items(request):

    account = account_from_params(request.query_params)
    goodparams = ItemsQueryType({k: v for (k, v)
                                 in request.query_params.items()
                                 if v != '*'})

    result = search_items(goodparams)
    log.debug('cache size: %d' % search_cache.currsize)
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
        task = BackgroundTask(track,
                              request=request,
                              results=rv,
                              api_key=account.key,
                              title='Item search results')
    else:
        task = None

    return response_object(rv, goodparams, task)


async def specific_item(request):

    for k in request.query_params.items():        # list of tuples
        if k[0] != 'callback' and k[0] != 'api_key':
            raise HTTPException(400, 'Unrecognized parameter %s' % k[0])

    id_or_ids = request.path_params['id_or_ids']
    account = account_from_params(request.query_params)
    goodparams = ItemsQueryType({k: v for [k, v]
                                 in request.query_params.items()})
    ids = id_or_ids.split(',')
    for the_id in ids:
        if not re.match(r'[a-f0-9]{32}$', the_id):
            raise HTTPException(400, "Bad ID: %s" % the_id)
    goodparams.update({'ids': ids})
    goodparams['page_size'] = len(ids)

    result = search_items(goodparams)
    log.debug('cache size: %d' % search_cache.currsize)

    if result['hits']['total'] == 0:
        raise HTTPException(404)

    rv = {
        'count': result['hits']['total'],
        'docs': [hit['_source'] for hit in result['hits']['hits']]
    }

    if account and not account.staff:
        task = BackgroundTask(track,
                              request=request,
                              results=rv,
                              api_key=account.key,
                              title='Fetch items')
    else:
        task = None

    return response_object(rv, goodparams, task)


async def mlt(request):
    """'More Like This' items"""

    id_or_ids = request.path_params['id_or_ids']
    account = account_from_params(request.query_params)
    goodparams = MLTQueryType({k: v for [k, v]
                               in request.query_params.items()})
    ids = id_or_ids.split(',')

    for the_id in ids:
        if not re.match(r'[a-f0-9]{32}$', the_id):
            raise HTTPException(400, "Bad ID: %s" % the_id)
    goodparams.update({'ids': ids})

    result = mlt_items(goodparams)
    log.debug('cache size: %d' % mlt_cache.currsize)

    rv = {
        'count': result['hits']['total'],
        'start': (int(goodparams['page']) - 1)
                  * int(goodparams['page_size'])               # noqa: E131
                  + 1,                                         # noqa: E131
        'limit': int(goodparams['page_size']),
        'docs': [compact(hit['_source'], goodparams)
                 for hit in result['hits']['hits']]
    }

    if account and not account.staff:
        track(request, rv, account.key, 'More-Like-This search results')

    return response_object(rv, goodparams)


async def api_key(request):
    """Create a new API key"""

    email = request.path_params['email']

    if not re.match(ok_email_pat, email):
        raise HTTPException(400, 'Bad email address')

    try:
        db.connect()
    except (OperationalError, ValueError):
        db.close()  # Must do this to release it to the connection pool
        log.exception('Failed to connect to database')
        raise HTTPException(503, 'Can not create API key')

    try:
        old_acct = Account.get(
            Account.email == email, Account.enabled == True)  # noqa: E712
        send_reminder_email(email, old_acct.key)
        db.close()
        raise HTTPException(409, 'There is already an API key for %s.  We have'
                                 ' sent a reminder message to that address.'
                                 % email)
    except DoesNotExist:
        # We want for it not to exist yet.
        # Keep the database connection open.
        pass

    new_key = secrets.token_hex(16)
    try:
        with db.atomic():
            Account(key=new_key, email=email, enabled=True).save()
            # This is not a BackgroundTask() because we don't want to claim
            # success to the user unless we know that the email was sent
            # without error.
            send_api_key_email(email, new_key)
    finally:
        db.close()

    return JSONResponse('API key created and sent to %s' % email)


async def suggestion(params: http.QueryParams,
                     request: http.Request) -> dict:
    """Suggestions for alternatives to the given text"""

    try:
        goodparams = SuggestionQueryType({k: v for [k, v] in params})
        q = SuggestionQuery(goodparams)
        resp = requests.post("%s/_search" % dplaapi.ES_BASE, json=q.query)
        resp.raise_for_status()

        result = resp.json()
        rv = {}

        for field in result['suggest'].keys():
            suggestion_list = []
            for ngram_result in result['suggest'][field]:
                for option in ngram_result['options']:
                    suggestion_list.append(option['text'])
            rv[field] = suggestion_list

        return response_object(rv, goodparams)

    except requests.exceptions.HTTPError:
        log.exception('Error querying Elasticsearch')
        raise HTTPException(503, 'Backend suggestion search operation failed')

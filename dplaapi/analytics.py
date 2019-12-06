import os
import requests
import logging
from urllib.parse import urlparse, quote_plus


"""
analytics.py
~~~~~~~~~~~~

Analytics logging.

Currently employs Google Analytics to collect usage information.

See https://developers.google.com/analytics/devguides/collection/protocol/v1/reference # noqa E501
"""

single_url = 'https://www.google-analytics.com/collect'
batch_url = 'http://www.google-analytics.com/batch'

log = logging.getLogger(__name__)


class GATracker():
    def __init__(self, tid, request, results, api_key, title):
        """
        Arguments:

        tid:      Google Analytics tracking ID
        request:  Starlette Request object
        results:  dict of the JSON result that's returned to the client
        api_key:  The API key
        title:    Title of the particular API endpoint
        """
        self.tid = tid
        self.request = request
        self.results = results
        self.api_key = api_key
        self.title = title
        u = urlparse(str(self.request.url))
        self.fullpath = '?'.join([u.path, u.query])
        self.host = u.netloc

    def run(self):
        """Track "pageview" and track event for an API request"""
        self.track_pageview()
        self.track_events()
        log.debug('GATracker done')

    def track_pageview(self):
        pv_data = [('t', 'pageview'), ('dh', self.host), ('dp', self.fullpath),
                   ('dt', self.title), ('cid', self.api_key)]
        body = self.payload_string(pv_data)
        post(single_url, body)
        log.debug('post url: %s' % single_url)
        log.debug('post body: %s' % body)

    def track_events(self):
        batch = "\n".join([self.payload_string(self.event(d))
                           for d in self.results['docs']])
        post(batch_url, batch)
        log.debug('post url: %s' % batch_url)
        log.debug('post body: %s' % batch)

    def event(self, doc):
        """Return a list for one event (item "document" seen in the response)

        Arguments:

        doc: An Elasticsearch 'doc' array element from the result
        """
        provider = doc.get('provider', {})
        provider_name = comma_del_string(provider.get('name', []))
        data_provider = comma_del_string(doc.get('dataProvider', []))
        sr = doc.get('sourceResource', {})
        title = comma_del_string(sr.get('title', []))
        return [('t', 'event'), ('cid', self.api_key),
                ('ec', 'View API Item : %s' % provider_name),
                ('ea', data_provider),
                ('el', '%s : %s' % (doc.get('id', ''), title)),
                ('dh', self.host), ('dp', self.fullpath)]

    def payload_string(self, tuple_list):
        tuple_list.append(('v', '1'))
        tuple_list.append(('tid', self.tid))
        return '&'.join(['%s=%s' % (k, quote_plus(v))
                         for (k, v) in tuple_list])


def comma_del_string(list_or_string):
    if isinstance(list_or_string, str):
        s = [list_or_string]
    else:
        s = list_or_string
    return ', '.join(s)


async def track(request, results, api_key, title):
    tid = os.getenv('GA_TID')
    if tid:
        GATracker(tid, request, results, api_key, title).run()


def post(url, body):
    try:
        resp = requests.post(url, data=body)
        resp.raise_for_status()
    except Exception:
        log.exception('Failed to post to Google Analytics')

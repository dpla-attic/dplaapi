"""
dplaapi
~~~~~~~

A web API for querying the Digital Public Library of America's metadata
"""

__version__ = '0.1.0'


import logging
from apistar import ASyncApp
from . import routes
from . import event_hooks

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)-15s] [%(process)d] [%(levelname)s] '
                           '[%(module)s]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %z')
log = logging.getLogger(__name__)

ES_BASE='http://internal-search-lbal-prod-es6-673529119.us-east-1.elb.' \
        'amazonaws.com:9200/dpla_alias'


# FIXME:
# For now, don't use event hooks because they prevent API Star from serving
# a 404 Not Found error for a request that doesn't match one of our routes.
# A 500 Server Error will be returned, instead.
# app = ASyncApp(routes=routes.routes, event_hooks=event_hooks.event_hooks)
app = ASyncApp(routes=routes.routes)

"""
dplaapi
~~~~~~~

A web API for querying the Digital Public Library of America's metadata
"""

__version__ = '0.1.0'

import os
import logging
from apistar import ASyncApp
from . import routes

log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

logging.basicConfig(level=log_levels[os.getenv('APP_LOG_LEVEL', 'debug')],
                    format='[%(asctime)-15s] [%(process)d] [%(levelname)s] '
                           '[%(module)s]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %z')
log = logging.getLogger(__name__)

ES_BASE = os.getenv('ES_BASE')
if ES_BASE is None:
    log.warning('ES_BASE env var is not defined. Elasticsearch queries will '
                'not work!')


# FIXME:
# For now, don't use event hooks because they prevent API Star from serving
# a 404 Not Found error for a request that doesn't match one of our routes.
# A 500 Server Error will be returned, instead.
# app = ASyncApp(routes=routes.routes, event_hooks=event_hooks.event_hooks)
app = ASyncApp(routes=routes.routes)

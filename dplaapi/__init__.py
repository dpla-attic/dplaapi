"""
dplaapi
~~~~~~~

A web API for querying the Digital Public Library of America's metadata
"""

__version__ = '2.2.0'

import os
import logging
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Router
from apistar.exceptions import ValidationError
from dplaapi.responses import JSONResponse
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
if not ES_BASE:
    log.warning('ES_BASE env var is not defined. Elasticsearch queries will '
                'not work!')


def http_exception_handler(request, exc):
    # We assume that an HTTPException, which has been raised by our code,
    # has already been logged.
    return JSONResponse(exc.detail, status_code=exc.status_code)


def validation_exception_handler(request, exc):
    return JSONResponse(exc.messages, status_code=400)


def misc_exception_handler(request, exc):
    log.exception(exc)
    return JSONResponse('Unexpected error', status_code=500)


app = Starlette(debug=False)
app.mount('', Router(routes.routes))
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, misc_exception_handler)
app.add_middleware(CORSMiddleware,
                   allow_origins=['*'],
                   allow_methods=['GET', 'POST'])

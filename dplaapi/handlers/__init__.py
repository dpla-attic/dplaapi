
import os
import logging
import apistar
from dplaapi.exceptions import ServerError


log = logging.getLogger(__name__)


async def redir_to_recent_version() -> dict:
    """Redirect to the most recent version of the API, /items endpoint"""
    try:
        headers = {'Location': '/v2/items'}
        data = headers
        return apistar.http.JSONResponse(data, status_code=301,
                                         headers=headers)
    except Exception as e:
        log.exception('Unexpected error')
        raise ServerError('Unexpected error')


async def request_info(request: apistar.http.Request) -> dict:
    """Get information about the request"""
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')}


async def sysinfo() -> dict:
    """Get system information"""
    if os.getenv('DEBUG_SYSINFO'):
        return {
            'cpus': os.cpu_count(),
            'pid': os.getpid(),
            'ppid': os.getppid()}
    else:
        raise apistar.exceptions.Forbidden()


import logging
import apistar


log = logging.getLogger(__name__)


async def redir_to_recent_version() -> dict:
    """Redirect to the most recent version of the API, /items endpoint"""
    headers = {'Location': '/v2/items'}
    data = headers
    return apistar.http.JSONResponse(data, status_code=301,
                                     headers=headers)

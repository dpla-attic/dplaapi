
import logging
from starlette.responses import RedirectResponse


log = logging.getLogger(__name__)


async def redir_to_recent_version(request):
    """Redirect to the most recent version of the API, /items endpoint"""
    return RedirectResponse(status_code=301, url='/v2/items')

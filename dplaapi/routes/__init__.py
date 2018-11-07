
from starlette.routing import Router, Route, Mount
from dplaapi import handlers
from dplaapi.handlers import v2 as v2_handlers
from . import v2 as v2_routes


routes = [
    Route('/',
          methods=['GET'],
          endpoint=handlers.redir_to_recent_version),
    Mount('/v2', app=Router(v2_routes.routes)),
    # These paths go to the most recent protocol version of the API; in this
    # case, /v2:
    Route('/items',
          methods=['GET', 'OPTIONS'],
          endpoint=v2_handlers.multiple_items),
    Route('/items/{id_or_ids}',
          methods=['GET', 'OPTIONS'],
          endpoint=v2_handlers.specific_item),
]

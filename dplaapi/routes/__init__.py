
from apistar import Route, Include
from dplaapi import handlers
from dplaapi.handlers import v2 as v2_handlers
from . import v2 as v2_routes


routes = [
    Route('/', method='GET', handler=handlers.redir_to_recent_version),
    Include('/v2', name='/v2', routes=v2_routes.routes),
    # These paths go to the most recent protocol version of the API; in this
    # case, /v2:
    Route('/items', method='GET', handler=v2_handlers.multiple_items),
    Route('/items/{id_or_ids}', method='GET',
          handler=v2_handlers.specific_item),
]

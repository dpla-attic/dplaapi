from starlette.routing import Route
from dplaapi.handlers import v2 as handlers


routes = [
    Route('/items',
          methods=['GET', 'OPTIONS'],
          endpoint=handlers.multiple_items),
    Route('/items/{id_or_ids}',
          methods=['GET', 'OPTIONS'],
          endpoint=handlers.specific_item),
    Route('/items/{id_or_ids}/mlt',
          methods=['GET', 'OPTIONS'],
          endpoint=handlers.mlt),
    Route('/api_key/{email}',
          methods=['POST', 'OPTIONS'],
          endpoint=handlers.api_key),
    Route('/suggestion',
          methods=['GET'],
          endpoint=handlers.suggestion)
]

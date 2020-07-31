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
    Route('/necropolis/{single_id}',
          methods=['GET', 'OPTIONS'],
          endpoint=handlers.specific_necropolis_item),
    Route('/api_key/{email}',
          methods=['POST', 'OPTIONS'],
          endpoint=handlers.api_key),
    Route('/random',
          methods=['GET', 'OPTIONS'],
          endpoint=handlers.random)
]

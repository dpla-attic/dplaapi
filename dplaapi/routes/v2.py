from apistar import Route
from dplaapi.handlers import v2 as handlers


routes = [
    Route('/items', method='GET', handler=handlers.multiple_items),
    Route('/items/{id_or_ids}', method='GET', handler=handlers.specific_item),
    Route('/items/{id_or_ids}/mlt', method='GET', handler=handlers.mlt),
    Route('/api_key/{email}', method='POST', handler=handlers.api_key),
    Route('/api_key', method='OPTIONS', handler=handlers.api_key_options)
]

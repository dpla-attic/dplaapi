from apistar import Route
from dplaapi.handlers import v2 as handlers


routes = [
    Route('/items', method='GET', handler=handlers.multiple_items),
    Route('/items/{record_id}', method='GET', handler=handlers.specific_item)
]

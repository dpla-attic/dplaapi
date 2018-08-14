from apistar import Route
from dplaapi.handlers import v2 as handlers


routes = [
    Route('/items', method='GET', handler=handlers.items)
]


from apistar import Route
from . import handlers


routes = [
    Route('/', method='GET', handler=handlers.index),
    Route('/req-info', method='GET', handler=handlers.request_info),
    Route('/search', method='GET', handler=handlers.search)
]

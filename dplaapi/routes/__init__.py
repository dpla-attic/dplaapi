
from apistar import Route, Include
from dplaapi import handlers
from . import v2 as v2_routes


routes = [
    Route('/', method='GET', handler=handlers.redir_to_recent_version),
    Route('/req-info', method='GET', handler=handlers.request_info),
    Route('/sysinfo', method='GET', handler=handlers.sysinfo),
    Include('/v2', name='/v2', routes=v2_routes.routes)
]

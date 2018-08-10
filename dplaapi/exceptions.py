
from apistar import exceptions


class ServerError(exceptions.HTTPException):
    default_status_code = 500
    default_detail = 'Internal Server Error'

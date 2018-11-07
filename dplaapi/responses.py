import starlette.responses


class JSONResponse(starlette.responses.JSONResponse):
    media_type = 'application/json; charset=utf-8'


class JavascriptResponse(starlette.responses.Response):
    media_type = 'application/javascript; charset=utf-8'

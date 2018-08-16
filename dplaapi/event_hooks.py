"""
Event hooks

As of apistar version 0.5.40, these event hooks interfere with the delivery of
404 Not Found errors. You can inspect the exception in an on_response or
on_error handler and find that its `status_code` is 404, but API Star serves
up a 500 Server Error.
"""

# import logging
# import time
# from apistar import http


# log = logging.getLogger(__name__)


# class TimingHook:
#     """Log internal processing time"""
#     def on_request(self, request: http.Request):
#         self.started = time.time()

#     def on_response(self):
#         duration = time.time() - self.started
#         log.debug("Time: %0.6f seconds" % duration)


# class ResponseHeadersHook:
#     def on_response(self, response: http.Response, exc: Exception):
#         response.headers['x-test'] = 'ok'


# class ErrorWrapupHook:
#     """
#     Cleanup or messaging after an exception has been handled
#     """
#     def on_response(self, response: http.Response, exc: Exception):
#         """Document the response given back to the user"""
#         if exc is not None:
#             log.error("Responded with %s" % exc.__class__)
#             log.error(response.status_code)
#             return True


# event_hooks = [
#     TimingHook,
#     ResponseHeadersHook,
#     ErrorWrapupHook
# ]

"""The HTTP layer.

These files are the only ones in the project allowed to know that HTTP exists:
status codes, request bodies, JSON, tokens in headers. A route reads the
request, calls one service method, and returns the result. Nothing else.

If you ever find an `if` in here that is about the *domain* rather than about
the request, it is in the wrong file -- it belongs in a service.
"""

from flask import current_app


def services():
    """The Services object that create_app() built and parked on the app.

    Looked up per request rather than imported at module level, because the
    services belong to one app and the test suite builds a new app every time.
    """
    return current_app.extensions["services"]

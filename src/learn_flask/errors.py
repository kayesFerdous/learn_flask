"""Errors the service layer raises, and the one handler that turns them into JSON.

Services raise these instead of calling flask_smorest's abort(), so nothing
below the HTTP layer needs Flask to be running.
"""

from werkzeug.http import HTTP_STATUS_CODES


class StoreAPIError(Exception):
    status_code = 500
    message = "Something went wrong."

    def __init__(self, message=None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(StoreAPIError):
    status_code = 404
    message = "Resource not found."


class ConflictError(StoreAPIError):
    status_code = 409
    message = "That conflicts with something that already exists."


class AuthenticationError(StoreAPIError):
    status_code = 401
    message = "Invalid email or password."


# Not PermissionError -- Python already has a builtin by that name.
class ForbiddenError(StoreAPIError):
    status_code = 403
    message = "You are not allowed to do that."


class BusinessRuleError(StoreAPIError):
    """Well-formed request that breaks a rule marshmallow cannot check."""

    status_code = 422
    message = "That request breaks a rule."


# 503, not 500: "try again shortly" rather than "this app is broken".
class ServiceUnavailableError(StoreAPIError):
    status_code = 503
    message = "The service is temporarily unavailable."


def register_error_handlers(app):
    # The shape matches flask-smorest's own errors, so clients parse one format.
    @app.errorhandler(StoreAPIError)
    def handle_store_api_error(error):
        return {
            "code": error.status_code,
            "status": HTTP_STATUS_CODES.get(error.status_code, "Unknown Error"),
            "message": error.message,
        }, error.status_code

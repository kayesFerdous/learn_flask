"""The errors the service layer is allowed to raise, and the one place that
turns them into HTTP responses.

Why not just call flask_smorest's abort() inside the services? Because abort()
is a Flask function. The moment a service calls it, the service needs Flask to
be installed, an app to be running, and a request to be in flight -- and then it
can only ever be used from a web request. It could not be reused by a CLI
command, a background worker, or a test.

So the rule is:

    services raise      ->      one handler here translates      ->      JSON

That is Dependency Inversion in its smallest possible form. The inner layer
(services) knows nothing about the outer layer (HTTP). The outer layer does all
the knowing.
"""

from werkzeug.http import HTTP_STATUS_CODES


class StoreAPIError(Exception):
    """Base class for everything the service layer raises on purpose.

    Subclasses only change two class attributes. Catching StoreAPIError catches
    all of them, which is what lets one error handler cover the whole app.
    """

    status_code = 500
    message = "Something went wrong."

    def __init__(self, message=None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(StoreAPIError):
    status_code = 404
    message = "Resource not found."


class ConflictError(StoreAPIError):
    """Something already exists, or the request fights with the current state."""

    status_code = 409
    message = "That conflicts with something that already exists."


class AuthenticationError(StoreAPIError):
    """We do not know who you are. Wrong password, bad token."""

    status_code = 401
    message = "Invalid email or password."


class ForbiddenError(StoreAPIError):
    """We know who you are, and you are not allowed to do this.

    Named ForbiddenError and not PermissionError because Python already has a
    builtin called PermissionError -- shadowing it would be a nasty surprise.
    """

    status_code = 403
    message = "You are not allowed to do that."


class BusinessRuleError(StoreAPIError):
    """The request is well-formed but breaks a rule of the domain.

    Marshmallow already rejects input that is the wrong *shape* (missing field,
    text where a number belongs). This is for rules marshmallow cannot know:
    "a tag and an item must belong to the same store", "not enough stock".
    """

    status_code = 422
    message = "That request breaks a rule."


def register_error_handlers(app):
    """Teach the app to answer every StoreAPIError with the same JSON shape.

    The shape matches what flask-smorest's own abort() produces, so a 404 raised
    by a service and a 422 raised by schema validation look identical to whoever
    is calling the API. Consistency here is worth more than it looks: clients
    only have to write one error-parsing branch.
    """

    @app.errorhandler(StoreAPIError)
    def handle_learn_flask_error(error):
        return {
            "code": error.status_code,
            "status": HTTP_STATUS_CODES.get(error.status_code, "Unknown Error"),
            "message": error.message,
        }, error.status_code

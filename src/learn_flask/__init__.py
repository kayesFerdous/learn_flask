"""The application factory.

create_app() builds one Flask app and returns it. It decides nothing: the
settings come from config.py, the rules live in services/, the sending of email
lives in notifications/. This file only wires those pieces to each other.

That makes it the composition root -- the single place where concrete classes
are chosen. Everywhere else in the app works with whatever it was handed, which
is what lets the same code run against Brevo, against your terminal, or against
nothing at all.
"""

import redis
from flask import Flask
from flask_smorest import Api
from rq import Queue

from learn_flask.config import get_config
from learn_flask.errors import register_error_handlers
from learn_flask.extensions import db, jwt, migrate
from learn_flask.notifications import build_email_sender
from learn_flask.resources.health import health_blp
from learn_flask.resources.item import item_blp
from learn_flask.resources.store import store_blp
from learn_flask.resources.tag import tag_blp
from learn_flask.resources.user import user_blp
from learn_flask.services import build_services


def create_app(config=None):
    """Build one Flask app.

    config: any object from learn_flask.config. Leave it out and APP_ENV decides
            (development by default).
    """
    app = Flask(__name__)
    app.config.from_object(config or get_config())

    db.init_app(app)
    migrate.init_app(app, db)

    _init_services(app)
    _init_jwt(app)
    register_error_handlers(app)
    _register_blueprints(app)

    return app


def _init_services(app):
    """Choose the email strategy, build the services, park them on the app.

    Read the two lines below and you know how the whole app is assembled. That
    is the point of keeping construction in one place: there is no hunting
    through five files to find out what UserService is actually emailing with.
    """
    queue = _build_queue(app.config)
    email_sender = build_email_sender(app.config, queue)

    # app.extensions is Flask's standard place to park things like this;
    # assigning app.services directly risks colliding with a future Flask
    # attribute.
    app.extensions["services"] = build_services(db.session, email_sender)


def _build_queue(config):
    """An rq queue, or None when Redis is not configured.

    Without the guard, redis.from_url(None) blows up and takes the whole app
    with it -- and local dev and the test suite have no Redis. Returning None
    is not a failure: build_email_sender() reads it as "send inline instead".
    """
    redis_url = config.get("REDIS_URL")
    if not redis_url:
        return None
    return Queue("email", connection=redis.from_url(redis_url))


def _init_jwt(app):
    """Attach JWTManager and teach it how to spot a revoked token."""
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        # Runs on every @jwt_required() request. True means "reject this token".
        return app.extensions["services"].users.is_token_revoked(jwt_payload["jti"])

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return {"message": "This token has been revoked. Please log in again."}, 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token(jwt_header, jwt_payload):
        return {"message": "This action needs a fresh token. Please log in again."}, 401


def _register_blueprints(app):
    """Hand every blueprint to flask-smorest so it can build the OpenAPI spec.

    Api() is built per-app rather than living in extensions.py, because it owns
    that app's API document. A shared one would collect duplicate paths every
    time create_app() ran again.
    """
    api = Api(app)

    api.register_blueprint(health_blp)
    api.register_blueprint(store_blp)
    api.register_blueprint(item_blp)
    api.register_blueprint(tag_blp)
    api.register_blueprint(user_blp)

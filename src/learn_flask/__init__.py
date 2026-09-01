import redis
from flask import Flask
from flask_smorest import Api
from rq import Queue

from learn_flask.config import Config
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
    app = Flask(__name__)
    app.config.from_object(config or Config())

    db.init_app(app)
    migrate.init_app(app, db)

    _init_services(app)
    _init_jwt(app)
    register_error_handlers(app)
    _register_blueprints(app)

    return app


def _init_services(app):
    queue = _build_queue(app.config)
    email_sender = build_email_sender(app.config, queue)
    app.extensions["services"] = build_services(db.session, email_sender)


def _build_queue(config):
    # redis.from_url(None) blows up, and local dev has no Redis. Returning None
    # is not a failure: build_email_sender() reads it as "send inline".
    redis_url = config.get("REDIS_URL")
    if not redis_url:
        return None
    return Queue("email", connection=redis.from_url(redis_url))


def _init_jwt(app):
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        return app.extensions["services"].users.is_token_revoked(jwt_payload["jti"])

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return {"message": "This token has been revoked. Please log in again."}, 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token(jwt_header, jwt_payload):
        return {"message": "This action needs a fresh token. Please log in again."}, 401


def _register_blueprints(app):
    # Api() is per-app, not in extensions.py: a shared one would collect
    # duplicate paths every time create_app() ran again.
    api = Api(app)

    api.register_blueprint(health_blp)
    api.register_blueprint(store_blp)
    api.register_blueprint(item_blp)
    api.register_blueprint(tag_blp)
    api.register_blueprint(user_blp)

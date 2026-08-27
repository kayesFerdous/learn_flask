import os
from datetime import timedelta

import redis
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api
from rq import Queue

from learn_flask.blueprints.item import item_blp
from learn_flask.blueprints.store import store_blp
from learn_flask.blueprints.tag import tag_blp
from learn_flask.blueprints.user import user_blp
from learn_flask.extensions import db
from learn_flask.models import TokenBlocklistModel


def create_app():

    app = Flask(__name__)

    # Only build a queue if Redis is actually configured. Without this guard
    # redis.from_url(None) blows up and takes the whole app with it -- and
    # local dev / tests have no Redis. tasks.py falls back to sending inline.
    #
    # app.extensions is Flask's standard place for this; assigning app.queue
    # directly risks colliding with a future Flask attribute.
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        app.extensions["rq_queue"] = Queue(
            "email", connection=redis.from_url(redis_url)
        )

    app.config["API_TITLE"] = "Store API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.1.0"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )
    app.config["API_SPEC_OPTIONS"] = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        }
    }
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///data.db"
    )

    # Serverless Postgres (Neon) suspends the database when idle, which kills
    # every pooled connection. pool_pre_ping checks a connection is still alive
    # before handing it to a request and silently replaces it if not -- without
    # this you get a random OperationalError on the first request after a quiet
    # period. Harmless against the local Postgres container too, so it needs no
    # dev/prod branching.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Dev-only fallback. In production JWT_SECRET_KEY must come from the
    # environment -- anyone who knows it can forge a token for any user.
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", "dev-only-secret-not-for-production-use-32b"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    db.init_app(app)
    migrate = Migrate(app, db)

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        # Runs on every @jwt_required() request. True means "reject this token".
        return db.session.get(TokenBlocklistModel, jwt_payload["jti"]) is not None

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return {"message": "This token has been revoked. Please log in again."}, 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token(jwt_header, jwt_payload):
        return {"message": "This action needs a fresh token. Please log in again."}, 401

    api = Api(app)

    # NOTE: No need to use this as, we are using alembic
    # with app.app_context():
    #     db.create_all()

    api.register_blueprint(store_blp)
    api.register_blueprint(item_blp)
    api.register_blueprint(tag_blp)
    api.register_blueprint(user_blp)

    return app

import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_smorest import Api

from learn_flask.blueprints.item import item_blp
from learn_flask.blueprints.store import store_blp
from learn_flask.blueprints.tag import tag_blp
from learn_flask.blueprints.user import user_blp
from learn_flask.extensions import db


def create_app():

    app = Flask(__name__)

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

    # Dev-only fallback. In production JWT_SECRET_KEY must come from the
    # environment -- anyone who knows it can forge a token for any user.
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", "dev-only-secret-not-for-production-use-32b"
    )

    db.init_app(app)
    JWTManager(app)

    api = Api(app)

    with app.app_context():
        db.create_all()

    api.register_blueprint(store_blp)
    api.register_blueprint(item_blp)
    api.register_blueprint(tag_blp)
    api.register_blueprint(user_blp)

    return app

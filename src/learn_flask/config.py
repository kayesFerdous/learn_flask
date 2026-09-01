import os
from datetime import timedelta


class Config:
    API_TITLE = "Store API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.1.0"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_JSON_PATH = "openapi.json"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    API_SPEC_OPTIONS = {
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

    PROPAGATE_EXCEPTIONS = True

    # Neon suspends the database when idle, which kills every pooled connection.
    # pool_pre_ping replaces a dead one instead of failing the request.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Read the environment in __init__, not in the class body. A class body runs
    # at import time, before main() has loaded .env.
    def __init__(self):
        production = os.getenv("APP_ENV") == "production"
        database_url = os.getenv("DATABASE_URL")
        jwt_secret = os.getenv("JWT_SECRET_KEY")

        # The fallbacks below are committed to git, so anyone could forge a
        # token. Crash instead of booting with them on a real server.
        if production:
            missing = [
                name
                for name, value in (
                    ("DATABASE_URL", database_url),
                    ("JWT_SECRET_KEY", jwt_secret),
                )
                if not value
            ]
            if missing:
                raise RuntimeError(
                    "Refusing to start in production without: " + ", ".join(missing)
                )

        self.DEBUG = not production
        self.SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///data.db"
        self.JWT_SECRET_KEY = jwt_secret or "dev-only-secret-not-for-production-32b"

        # No Redis means no background queue, so the email is sent inline.
        self.REDIS_URL = os.getenv("REDIS_URL")

        # No Brevo key means print the email instead of sending it, so a fresh
        # clone runs with no accounts to set up.
        self.BREVO_API_KEY = os.getenv("BREVO_API_KEY")
        self.MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "")
        self.MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Store API")
        self.EMAIL_BACKEND = os.getenv(
            "EMAIL_BACKEND", "brevo" if self.BREVO_API_KEY else "console"
        )

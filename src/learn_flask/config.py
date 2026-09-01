from datetime import timedelta

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_DATABASE = "sqlite:///data.db"
DEV_JWT_SECRET = "dev-only-secret-not-for-production-32b"


class Settings(BaseSettings):
    # Reads .env itself, so `uv run server` and gunicorn both see it. Names are
    # already uppercase because Flask ignores anything else in app.config.
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", populate_by_name=True
    )

    APP_ENV: str = "development"
    DEBUG: bool = False

    API_TITLE: str = "Store API"
    API_VERSION: str = "v1"
    OPENAPI_VERSION: str = "3.1.0"
    OPENAPI_URL_PREFIX: str = "/"
    OPENAPI_JSON_PATH: str = "openapi.json"
    OPENAPI_SWAGGER_UI_PATH: str = "/docs"
    OPENAPI_SWAGGER_UI_URL: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    API_SPEC_OPTIONS: dict = {
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
    PROPAGATE_EXCEPTIONS: bool = True

    # Flask-SQLAlchemy wants SQLALCHEMY_DATABASE_URI; the environment variable
    # everyone writes is DATABASE_URL. The alias bridges the two.
    SQLALCHEMY_DATABASE_URI: str = Field(default="", alias="DATABASE_URL")

    # Neon suspends the database when idle, killing every pooled connection.
    # pool_pre_ping replaces a dead one instead of failing the request.
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True, "pool_recycle": 300}

    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)

    # No Redis means no background queue, so the email is sent inline.
    REDIS_URL: str | None = None

    BREVO_API_KEY: str | None = None
    MAIL_FROM_EMAIL: str = ""
    MAIL_FROM_NAME: str = "Store API"
    EMAIL_BACKEND: str | None = None

    @model_validator(mode="after")
    def apply_environment_rules(self):
        production = self.APP_ENV == "production"

        if production:
            # The dev fallbacks below are committed to git, so anyone could
            # forge a token. Crash rather than boot with them on a real server.
            missing = [
                name
                for name, value in (
                    ("DATABASE_URL", self.SQLALCHEMY_DATABASE_URI),
                    ("JWT_SECRET_KEY", self.JWT_SECRET_KEY),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    "Refusing to start in production without: " + ", ".join(missing)
                )
        else:
            self.SQLALCHEMY_DATABASE_URI = (
                self.SQLALCHEMY_DATABASE_URI or DEV_DATABASE
            )
            self.JWT_SECRET_KEY = self.JWT_SECRET_KEY or DEV_JWT_SECRET

        self.DEBUG = not production

        # No Brevo key means print the email instead of sending it, so a fresh
        # clone runs with nothing to set up.
        if self.EMAIL_BACKEND is None:
            self.EMAIL_BACKEND = "brevo" if self.BREVO_API_KEY else "console"

        return self

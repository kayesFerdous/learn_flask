"""One configuration class per environment.

Flask keeps its settings in `app.config`. Before this file, every setting was
written inline in create_app() with a pile of os.getenv() calls. Moving them
here buys three things:

  * One place to look when you ask "how is this app configured?"
  * Tests get their own database and their own secret, without touching yours.
  * Production can REFUSE to start when a secret is missing, instead of quietly
    falling back to a value that is published on GitHub for anyone to read.

get_config() at the bottom is the Factory: you hand it a name, it hands back
the right config object. create_app() never has to know which one it got.
"""

import os
from datetime import timedelta


class BaseConfig:
    """Settings that are the same everywhere.

    Anything read from the environment goes in __init__, NOT in the class body.
    A class body runs the moment this file is imported, which is before main()
    has had a chance to load the .env file -- so values read up here would
    always come back empty. __init__ runs later, when get_config() is called.
    """

    # --- flask-smorest / OpenAPI docs -------------------------------------
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

    # --- Database ---------------------------------------------------------
    # Serverless Postgres (Neon) suspends the database when idle, which kills
    # every pooled connection. pool_pre_ping checks a connection is still alive
    # before handing it to a request and silently replaces it if not -- without
    # this you get a random OperationalError on the first request after a quiet
    # period. Harmless against the local Postgres container too, so it needs no
    # dev/prod branching.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    # --- JWT --------------------------------------------------------------
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    def __init__(self):
        #   postgresql+psycopg -> dialect + driver. The `+psycopg` is required;
        #   without it SQLAlchemy looks for psycopg2, which we do not install.
        self.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

        # Anyone who knows this can forge a token for any user.
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

        # No Redis configured means no background queue, and the email is sent
        # during the request instead. See notifications/queued.py.
        self.REDIS_URL = os.getenv("REDIS_URL")

        # --- Email -------------------------------------------------------
        # Which EmailSender strategy build_email_sender() should pick. Left
        # unset it works itself out: a Brevo key means send for real, no key
        # means print to the terminal. So a fresh clone runs with no accounts
        # and no setup, and signup still works.
        self.BREVO_API_KEY = os.getenv("BREVO_API_KEY")
        self.MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "")
        self.MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Store API")
        self.EMAIL_BACKEND = os.getenv("EMAIL_BACKEND") or (
            "brevo" if self.BREVO_API_KEY else "console"
        )


class DevConfig(BaseConfig):
    """Your machine. Everything has a fallback so the app runs with no setup."""

    DEBUG = True

    def __init__(self):
        super().__init__()
        # No DATABASE_URL? Use a local sqlite file. `uv run server` then works
        # on a fresh clone without starting docker compose first.
        self.SQLALCHEMY_DATABASE_URI = self.SQLALCHEMY_DATABASE_URI or "sqlite:///data.db"
        self.JWT_SECRET_KEY = (
            self.JWT_SECRET_KEY or "dev-only-secret-not-for-production-use-32b"
        )


class TestConfig(BaseConfig):
    """pytest. Nothing here touches the outside world.

    This class is the reason the config Factory is worth having: a test can
    build a complete, working app with one line and be certain it will not
    write to your real database or reach for Redis.
    """

    TESTING = True
    DEBUG = False

    def __init__(self):
        super().__init__()
        # ":memory:" is a database that lives in RAM and disappears when the
        # process ends. Every test run starts from an empty schema.
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        self.JWT_SECRET_KEY = "test-secret-not-used-outside-the-test-suite"
        # Deliberately ignore any REDIS_URL in the environment. A test must
        # never queue a real job, and must never send a real email.
        self.REDIS_URL = None
        self.EMAIL_BACKEND = "null"


class ProdConfig(BaseConfig):
    """Render, or any real server. Fails loudly instead of guessing."""

    DEBUG = False

    def __init__(self):
        super().__init__()
        # Fail fast. Before this check, a forgotten JWT_SECRET_KEY meant the
        # app booted happily using the dev fallback above -- a secret that is
        # committed to git, so every token it signs is forgeable. A crash on
        # startup is a much better outcome than a silent security hole.
        missing = [
            name
            for name, value in (
                ("DATABASE_URL", self.SQLALCHEMY_DATABASE_URI),
                ("JWT_SECRET_KEY", self.JWT_SECRET_KEY),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Refusing to start in production without: "
                + ", ".join(missing)
                + ". Set them in your host's environment settings."
            )


# The Factory's lookup table. Adding a new environment means adding a class and
# one line here -- no `if/elif` chain to edit anywhere else in the app.
CONFIGS = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}


def get_config(name=None):
    """Turn an environment name into a ready-to-use config object.

    Called with no arguments it reads APP_ENV, defaulting to development. So
    `uv run server` needs no setup, while the Dockerfile sets APP_ENV=production
    and gets the strict class.
    """
    name = name or os.getenv("APP_ENV", "development")
    config_class = CONFIGS.get(name)
    if config_class is None:
        raise RuntimeError(
            f"Unknown APP_ENV {name!r}. Valid values: {', '.join(CONFIGS)}."
        )
    return config_class()

"""The shared extension objects.

Each of these is created once, here, and imported everywhere else. That is the
Singleton pattern -- and in Python you get it for free, because a module is only
ever executed once no matter how many files import it. Writing a class with a
custom __new__ to "make a singleton" would be extra code for the same result.

They are built empty and attached to an app later with init_app(). That split is
what lets create_app() run more than once in a single process, which is exactly
what the test suite does: a fresh app, with a fresh database, for every test.
"""

from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()

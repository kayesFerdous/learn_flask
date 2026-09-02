from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Built empty here and attached to an app later with init_app(), so create_app()
# can run more than once in a single process.
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()

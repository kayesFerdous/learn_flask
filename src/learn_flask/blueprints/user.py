from flask.views import MethodView
from flask_jwt_extended import create_access_token, jwt_required
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError

from learn_flask.blueprints import get_user_or_404
from learn_flask.extensions import db
from learn_flask.models import UserModel
from learn_flask.schemas import (
    MessageSchema,
    TokenSchema,
    UserLoginSchema,
    UserSchema,
)

user_blp = Blueprint(
    "Users", "users", url_prefix="/users", description="Registration and login"
)


@user_blp.route("/")
class UserList(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema(many=True))
    def get(self):
        return db.session.scalars(db.select(UserModel)).all()

    @user_blp.arguments(UserSchema)
    @user_blp.response(201, UserSchema)
    def post(self, user_data):
        user = UserModel(
            name=user_data["name"],
            password_hash=pbkdf2_sha256.hash(user_data["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(400, message="A user with this name already exists.")

        return user


@user_blp.route("/login")
class UserLogin(MethodView):
    @user_blp.arguments(UserLoginSchema)
    @user_blp.response(200, TokenSchema)
    def post(self, user_data):
        user = db.session.scalar(
            db.select(UserModel).where(UserModel.name == user_data["name"])
        )
        if user is None or not pbkdf2_sha256.verify(
            user_data["password"], user.password_hash
        ):
            abort(401, message="Invalid username or password.")

        return {"access_token": create_access_token(identity=str(user.id))}


@user_blp.route("/<uuid:user_id>")
class User(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema)
    def get(self, user_id):
        return get_user_or_404(user_id)

    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, MessageSchema)
    def delete(self, user_id):
        user = get_user_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": f"User {user_id} deleted."}

from datetime import datetime, timezone

from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError

from learn_flask.blueprints import get_user_or_404
from learn_flask.extensions import db
from learn_flask.models import TokenBlocklistModel, UserModel
from learn_flask.schemas import (
    MessageSchema,
    TokenSchema,
    UserLoginSchema,
    UserSchema,
)

user_blp = Blueprint(
    "Users", "users", url_prefix="/users", description="Registration and login"
)


def revoke(token):
    """Block this token's jti, and drop rows for tokens that already expired."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Rows for tokens that have already expired can never block anything,
    # so drop them here instead of running a separate cleanup job.
    db.session.execute(
        db.delete(TokenBlocklistModel).where(TokenBlocklistModel.expires_at < now)
    )
    db.session.add(
        TokenBlocklistModel(
            jti=token["jti"],
            expires_at=datetime.fromtimestamp(token["exp"], tz=timezone.utc).replace(
                tzinfo=None
            ),
        )
    )


def reject_if_taken(name, email):
    if db.session.scalar(db.select(UserModel).where(UserModel.name == name)):
        abort(
            400,
            message=f"The username '{name}' already exists. Please pick another one.",
        )
    if db.session.scalar(db.select(UserModel).where(UserModel.email == email)):
        abort(400, message=f"An account with the email '{email}' already exists.")


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
        reject_if_taken(user_data["name"], user_data["email"])

        user = UserModel(
            name=user_data["name"],
            email=user_data["email"],
            password_hash=pbkdf2_sha256.hash(user_data["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # Two signups can clear the check above at the same moment and only
            # one can win. Re-checking finds whichever row got there first.
            reject_if_taken(user_data["name"], user_data["email"])
            raise

        return user


@user_blp.route("/login")
class UserLogin(MethodView):
    @user_blp.arguments(UserLoginSchema)
    @user_blp.response(200, TokenSchema)
    def post(self, user_data):
        user = db.session.scalar(
            db.select(UserModel).where(UserModel.email == user_data["email"])
        )
        if user is None or not pbkdf2_sha256.verify(
            user_data["password"], user.password_hash
        ):
            abort(401, message="Invalid email or password.")

        return {
            "access_token": create_access_token(identity=str(user.id), fresh=True),
            "refresh_token": create_refresh_token(identity=str(user.id)),
        }


@user_blp.route("/<uuid:user_id>")
class User(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema)
    def get(self, user_id):
        return get_user_or_404(user_id)

    @jwt_required(fresh=True)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, MessageSchema)
    def delete(self, user_id):
        user = get_user_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": f"User {user_id} deleted."}


@user_blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required(verify_type=False)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, MessageSchema)
    def post(self):
        token = get_jwt()
        revoke(token)
        db.session.commit()
        return {"message": f"Successfully revoked the {token['type']} token."}


@user_blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, TokenSchema)
    def post(self):
        identity = get_jwt_identity()

        # Rotation: the refresh token just used is retired and replaced, so a
        # stolen one stops working as soon as the real user refreshes.
        revoke(get_jwt())
        db.session.commit()

        return {
            "access_token": create_access_token(identity=identity, fresh=False),
            "refresh_token": create_refresh_token(identity=identity),
        }

"""Account routes.

Token creation stays here on purpose. A JWT is how *this API* proves who you
are over HTTP -- it is a transport detail, not a rule of the store. UserService
deals in users and passwords; it never sees a token.
"""

from datetime import datetime, timezone
from uuid import UUID

from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint

from learn_flask.resources import services
from learn_flask.schemas import (
    MessageSchema,
    TokenSchema,
    UserLoginSchema,
    UserSchema,
    UserUpdateSchema,
)

user_blp = Blueprint(
    "Users", "users", url_prefix="/users", description="Registration and login"
)


def _token_pair(identity, fresh):
    return {
        "access_token": create_access_token(identity=identity, fresh=fresh),
        "refresh_token": create_refresh_token(identity=identity),
    }


def _expires_at(token):
    """Turn the JWT's `exp` timestamp into the naive UTC datetime the table wants."""
    return datetime.fromtimestamp(token["exp"], tz=timezone.utc).replace(tzinfo=None)


@user_blp.route("/")
class UserList(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema(many=True))
    def get(self):
        return services().users.list_all()

    @user_blp.arguments(UserSchema)
    @user_blp.response(201, UserSchema)
    def post(self, user_data):
        return services().users.register(
            name=user_data["name"],
            email=user_data["email"],
            password=user_data["password"],
        )


@user_blp.route("/login")
class UserLogin(MethodView):
    @user_blp.arguments(UserLoginSchema)
    @user_blp.response(200, TokenSchema)
    def post(self, user_data):
        user = services().users.authenticate(
            user_data["email"], user_data["password"]
        )
        return _token_pair(str(user.id), fresh=True)


@user_blp.route("/<uuid:user_id>")
class User(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema)
    def get(self, user_id):
        return services().users.get(user_id)

    # fresh=True for the same reason delete uses it: changing an email or
    # password is account-takeover material, so a refreshed token is not enough.
    @jwt_required(fresh=True)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.arguments(UserUpdateSchema)
    @user_blp.response(200, UserSchema)
    def patch(self, user_data, user_id):
        return services().users.update(user_id, get_jwt_identity(), user_data)

    @jwt_required(fresh=True)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, MessageSchema)
    def delete(self, user_id):
        services().users.delete(user_id)
        return {"message": f"User {user_id} deleted."}


@user_blp.route("/me")
class CurrentUser(MethodView):
    @jwt_required()
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, UserSchema)
    def get(self):
        return services().users.get(UUID(get_jwt_identity()))


@user_blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required(verify_type=False)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, MessageSchema)
    def post(self):
        token = get_jwt()
        services().users.revoke_token(token["jti"], _expires_at(token))
        return {"message": f"Successfully revoked the {token['type']} token."}


@user_blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    @user_blp.doc(security=[{"bearerAuth": []}])
    @user_blp.response(200, TokenSchema)
    def post(self):
        token = get_jwt()

        # Rotation: the refresh token just used is retired and replaced, so a
        # stolen one stops working as soon as the real user refreshes.
        services().users.revoke_token(token["jti"], _expires_at(token))

        return _token_pair(get_jwt_identity(), fresh=False)

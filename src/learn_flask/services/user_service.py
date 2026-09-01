from datetime import datetime, timezone

from passlib.hash import pbkdf2_sha256
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from learn_flask.errors import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from learn_flask.models import TokenBlocklistModel, UserModel
from learn_flask.notifications import welcome_email


class UserService:
    def __init__(self, session, email_sender):
        self.session = session
        self.email_sender = email_sender

    def get(self, user_id):
        user = self.session.get(UserModel, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    def list_all(self):
        return self.session.scalars(select(UserModel)).all()

    def register(self, name, email, password):
        self._reject_if_taken(name, email)

        user = UserModel(
            name=name,
            email=email,
            password_hash=pbkdf2_sha256.hash(password),
        )
        try:
            self.session.add(user)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            # Two signups can clear the check above at the same moment and only
            # one can win. Re-checking finds whichever row got there first.
            self._reject_if_taken(name, email)
            raise

        self.email_sender.send(welcome_email(user.name, user.email))
        return user

    def authenticate(self, email, password):
        user = self.session.scalar(select(UserModel).where(UserModel.email == email))
        # Same error for both cases, or it tells an attacker which addresses
        # have accounts.
        if user is None or not pbkdf2_sha256.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        return user

    def update(self, user_id, actor_id, data):
        user = self.get(user_id)
        if str(user.id) != actor_id:
            raise ForbiddenError("You can only update your own account.")

        name, email = data.get("name"), data.get("email")
        self._reject_if_taken(name, email, exclude_id=user.id)

        if "password" in data:
            user.password_hash = pbkdf2_sha256.hash(data.pop("password"))
        for field, value in data.items():
            setattr(user, field, value)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            self._reject_if_taken(name, email, exclude_id=user.id)
            raise

        return user

    def delete(self, user_id):
        user = self.get(user_id)
        self.session.delete(user)
        self.session.commit()

    def revoke_token(self, jti, expires_at):
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Rows for expired tokens can never block anything, so drop them here
        # instead of running a separate cleanup job.
        self.session.execute(
            delete(TokenBlocklistModel).where(TokenBlocklistModel.expires_at < now)
        )
        self.session.add(TokenBlocklistModel(jti=jti, expires_at=expires_at))
        self.session.commit()

    def is_token_revoked(self, jti):
        return self.session.get(TokenBlocklistModel, jti) is not None

    def _reject_if_taken(self, name, email, exclude_id=None):
        # exclude_id skips one row, so updating a user does not collide with itself.
        def taken(column, value):
            query = select(UserModel).where(column == value)
            if exclude_id is not None:
                query = query.where(UserModel.id != exclude_id)
            return self.session.scalar(query) is not None

        if name is not None and taken(UserModel.name, name):
            raise ConflictError(
                f"The username '{name}' already exists. Please pick another one."
            )
        if email is not None and taken(UserModel.email, email):
            raise ConflictError(
                f"An account with the email '{email}' already exists."
            )

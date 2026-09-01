"""Business rules for accounts: registration, login, and token revocation.

This is the file worth showing in the presentation. Compare it to the old
blueprints/user.py, where all of this lived inside HTTP handlers.

Two things it does NOT import: Flask, and anything that knows about Brevo.
"""

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
        # An EmailSender, not a Brevo client. This class does not know whether
        # the email will go over the network, be printed to your terminal, or be
        # thrown away -- and it must not care. That is Dependency Inversion:
        # depend on the abstraction, never on the concrete thing.
        self.email_sender = email_sender

    # --- reading ----------------------------------------------------------

    def get(self, user_id):
        user = self.session.get(UserModel, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    def list_all(self):
        return self.session.scalars(select(UserModel)).all()

    # --- registration and login -------------------------------------------

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

        # The account already exists at this point. If the email fails, the
        # signup still succeeded -- which is why EmailSender.send() is required
        # never to raise.
        self.email_sender.send(welcome_email(user.name, user.email))

        return user

    def authenticate(self, email, password):
        user = self.session.scalar(select(UserModel).where(UserModel.email == email))
        # Deliberately the same error for "no such user" and "wrong password".
        # Two different messages would tell an attacker which email addresses
        # have accounts.
        if user is None or not pbkdf2_sha256.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        return user

    # --- changing an account ----------------------------------------------

    def update(self, user_id, actor_id, data):
        """actor_id is whoever is making the request, as a string."""
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
            # Same race as registration: another request can take the name or
            # email between the check above and the commit.
            self._reject_if_taken(name, email, exclude_id=user.id)
            raise

        return user

    def delete(self, user_id):
        user = self.get(user_id)
        self.session.delete(user)
        self.session.commit()

    # --- tokens -----------------------------------------------------------

    def revoke_token(self, jti, expires_at):
        """Block one token, and clean out rows for tokens that already expired.

        Takes a plain id and a datetime, not a JWT payload dict. Decoding the
        token is the HTTP layer's job; this method only stores the result.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Rows for tokens that have already expired can never block anything,
        # so drop them here instead of running a separate cleanup job.
        self.session.execute(
            delete(TokenBlocklistModel).where(TokenBlocklistModel.expires_at < now)
        )
        self.session.add(TokenBlocklistModel(jti=jti, expires_at=expires_at))
        self.session.commit()

    def is_token_revoked(self, jti):
        return self.session.get(TokenBlocklistModel, jti) is not None

    # --- internals --------------------------------------------------------

    def _reject_if_taken(self, name, email, exclude_id=None):
        """exclude_id skips one row, so updating a user does not collide with itself."""

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

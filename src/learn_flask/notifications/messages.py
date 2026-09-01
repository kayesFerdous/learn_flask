"""What the emails say.

Separate from *how* they are sent. Rewording the welcome email should never
mean opening a file that talks to Brevo, and vice versa -- that is Single
Responsibility applied to two things people wrongly lump together.
"""

from learn_flask.notifications.base import Email


def welcome_email(name: str, to_email: str) -> Email:
    return Email(
        to_email=to_email,
        to_name=name,
        subject="Welcome to the Store API",
        text=(
            f"Hi {name},\n\n"
            "Your Store API account is ready. You can log in at /users/login "
            "with this email address and the password you chose.\n\n"
            "-- The Store API"
        ),
        html=(
            f"<p>Hi {name},</p>"
            "<p>Your Store API account is ready. You can log in at "
            "<code>/users/login</code> with this email address and the "
            "password you chose.</p>"
            "<p>&mdash; The Store API</p>"
        ),
    )

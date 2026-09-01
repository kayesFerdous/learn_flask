"""Picking the email strategy.

build_email_sender() is a Factory, and it is deliberately the same shape as
get_config() in config.py: a lookup table, not an if/elif chain. Adding a
provider is one class in senders.py plus one line in BACKENDS below.
"""

from learn_flask.notifications.base import Email, EmailSender
from learn_flask.notifications.messages import welcome_email
from learn_flask.notifications.queued import QueuedSender, deliver
from learn_flask.notifications.senders import (
    BrevoSender,
    ConsoleSender,
    NullSender,
    RecordingSender,
)

__all__ = [
    "BrevoSender",
    "ConsoleSender",
    "Email",
    "EmailSender",
    "NullSender",
    "QueuedSender",
    "RecordingSender",
    "build_email_sender",
    "deliver",
    "welcome_email",
]


BACKENDS = {
    "brevo": lambda config: BrevoSender(
        api_key=config["BREVO_API_KEY"],
        from_email=config["MAIL_FROM_EMAIL"],
        from_name=config["MAIL_FROM_NAME"],
    ),
    "console": lambda config: ConsoleSender(),
    "null": lambda config: NullSender(),
}


def build_email_sender(config, queue=None):
    """Return the sender this app should use.

    config: anything dict-like. app.config in the web app, os.environ-derived
            settings in a worker. It is NOT a Flask app -- this function has no
            idea Flask exists, which is why a CLI or a worker could call it too.
    queue:  an rq Queue, or None. When present the chosen sender is wrapped in
            QueuedSender so the work happens in the background.
    """
    backend = config["EMAIL_BACKEND"]
    build = BACKENDS.get(backend)
    if build is None:
        raise RuntimeError(
            f"Unknown EMAIL_BACKEND {backend!r}. Valid values: {', '.join(BACKENDS)}."
        )

    sender = build(config)

    # NullSender in a queue would mean paying for a round trip to Redis to do
    # nothing at all, so skip the wrapper for it.
    if queue is not None and backend != "null":
        sender = QueuedSender(sender, queue)

    return sender

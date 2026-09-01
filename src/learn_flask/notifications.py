"""Sending email. One interface, three ways to satisfy it."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


@dataclass(frozen=True)
class Email:
    to_email: str
    to_name: str
    subject: str
    text: str
    html: str


class EmailSender(ABC):
    @abstractmethod
    def send(self, email: Email) -> None:
        """Must not raise. A failed welcome email is not a failed signup."""


class BrevoSender(EmailSender):
    def __init__(self, api_key, from_email, from_name):
        # Strings only, no httpx.Client: rq pickles this object to reach the
        # worker, and an open connection would not survive the trip.
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name

    def send(self, email):
        payload = {
            "sender": {"email": self.from_email, "name": self.from_name},
            "to": [{"email": email.to_email, "name": email.to_name}],
            "subject": email.subject,
            "textContent": email.text,
            "htmlContent": email.html,
        }
        try:
            response = httpx.post(
                BREVO_ENDPOINT,
                json=payload,
                headers={"api-key": self.api_key, "accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            log.warning(
                "Brevo rejected the email to %s: %s %s",
                email.to_email,
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.HTTPError as exc:
            log.warning("Could not reach Brevo to email %s: %s", email.to_email, exc)


class ConsoleSender(EmailSender):
    def send(self, email):
        log.info(
            "\n--- email (not sent) ---\nTo: %s <%s>\nSubject: %s\n\n%s\n",
            email.to_name,
            email.to_email,
            email.subject,
            email.text,
        )


def deliver(sender, email):
    """The function rq runs inside the worker process."""
    sender.send(email)


class QueuedSender(EmailSender):
    """Wraps any sender and hands the work to a background worker instead."""

    def __init__(self, inner, queue):
        self._inner = inner
        self._queue = queue

    def send(self, email):
        try:
            self._queue.enqueue(deliver, self._inner, email)
        except Exception as exc:
            # Redis being down must not fail a signup that already worked.
            log.warning("Could not queue the email to %s: %s", email.to_email, exc)
            self._inner.send(email)


BACKENDS = {
    "brevo": lambda c: BrevoSender(
        c["BREVO_API_KEY"], c["MAIL_FROM_EMAIL"], c["MAIL_FROM_NAME"]
    ),
    "console": lambda c: ConsoleSender(),
}


def build_email_sender(config, queue=None):
    build = BACKENDS.get(config["EMAIL_BACKEND"])
    if build is None:
        raise RuntimeError(
            f"Unknown EMAIL_BACKEND {config['EMAIL_BACKEND']!r}. "
            f"Valid values: {', '.join(BACKENDS)}."
        )
    sender = build(config)
    return QueuedSender(sender, queue) if queue is not None else sender


def welcome_email(name, to_email):
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

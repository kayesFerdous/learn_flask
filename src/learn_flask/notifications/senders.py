"""The concrete strategies. Each one is a different way to "send" an email.

Adding a provider means adding a class here and one line in __init__.py. No
existing class is touched, and no service or route changes. That is the
Open/Closed principle -- open to new behaviour, closed to being edited.
"""

import logging

import httpx

from learn_flask.notifications.base import Email, EmailSender

log = logging.getLogger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


class BrevoSender(EmailSender):
    """The real one. Posts the message to Brevo's transactional email API."""

    def __init__(self, api_key, from_email, from_name):
        # Plain strings only -- no httpx.Client stored here. rq pickles this
        # object to send it to the worker, and an open connection would not
        # survive the trip.
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name

    def send(self, email: Email) -> None:
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
        else:
            log.info("Email sent to %s", email.to_email)


class ConsoleSender(EmailSender):
    """Development. Prints the email instead of sending it.

    This is what makes the project runnable on a fresh clone with no accounts
    and no API keys: signup still works, and you can read the welcome message
    in your terminal.
    """

    def send(self, email: Email) -> None:
        log.info(
            "\n--- email (not actually sent) ---\n"
            "To:      %s <%s>\n"
            "Subject: %s\n\n%s\n"
            "--------------------------------",
            email.to_name,
            email.to_email,
            email.subject,
            email.text,
        )


class NullSender(EmailSender):
    """Tests. Does nothing at all.

    This class is the clearest proof the abstraction pays for itself: the whole
    signup flow can be tested without a network, an API key, or a mock library.
    """

    def send(self, email: Email) -> None:
        return None


class RecordingSender(EmailSender):
    """Tests that want to assert an email WAS sent, without sending one.

    Kept next to the real senders on purpose -- it is a strategy like any other,
    and Liskov substitution says it must work anywhere an EmailSender is
    expected. If it does not, the abstraction is wrong.
    """

    def __init__(self):
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)

import logging
import os

import httpx
from flask import current_app

log = logging.getLogger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def send_welcome_email(name, email):
    # Runs inside the rq worker, which has no Flask app -- so read the
    # environment directly instead of current_app.config.
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        log.info("BREVO_API_KEY not set -- skipping welcome email to %s", email)
        return

    payload = {
        "sender": {
            "email": os.getenv("MAIL_FROM_EMAIL", ""),
            "name": os.getenv("MAIL_FROM_NAME", "Store API"),
        },
        "to": [{"email": email, "name": name}],
        "subject": "Welcome to the Store API",
        "textContent": (
            f"Hi {name},\n\n"
            "Your Store API account is ready. You can log in at /users/login "
            "with this email address and the password you chose.\n\n"
            "-- The Store API"
        ),
        "htmlContent": (
            f"<p>Hi {name},</p>"
            "<p>Your Store API account is ready. You can log in at "
            "<code>/users/login</code> with this email address and the "
            "password you chose.</p>"
            "<p>&mdash; The Store API</p>"
        ),
    }

    try:
        response = httpx.post(
            BREVO_ENDPOINT,
            json=payload,
            headers={"api-key": api_key, "accept": "application/json"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        log.warning(
            "Brevo rejected the welcome email to %s: %s %s",
            email,
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.HTTPError as exc:
        log.warning("Could not reach Brevo to email %s: %s", email, exc)
    else:
        log.info("Welcome email sent to %s", email)


def enqueue_welcome_email(name, email):
    # Runs in the web request, which does have an app. No REDIS_URL means no
    # queue, so just send it here -- slower signup, but nothing to set up.
    queue = current_app.extensions.get("rq_queue")
    if queue is None:
        send_welcome_email(name, email)
        return

    queue.enqueue(send_welcome_email, name, email)

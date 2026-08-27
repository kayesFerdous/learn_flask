import logging

import httpx
from flask import current_app

log = logging.getLogger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def send_welcome_email(user):
    api_key = current_app.config.get("BREVO_API_KEY")
    if not api_key:
        log.info("BREVO_API_KEY not set -- skipping welcome email to %s", user.email)
        return

    payload = {
        "sender": {
            "email": current_app.config["MAIL_FROM_EMAIL"],
            "name": current_app.config["MAIL_FROM_NAME"],
        },
        "to": [{"email": user.email, "name": user.name}],
        "subject": "Welcome to the Store API",
        "textContent": (
            f"Hi {user.name},\n\n"
            "Your Store API account is ready. You can log in at /users/login "
            "with this email address and the password you chose.\n\n"
            "-- The Store API"
        ),
        "htmlContent": (
            f"<p>Hi {user.name},</p>"
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
            user.email,
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.HTTPError as exc:
        log.warning("Could not reach Brevo to email %s: %s", user.email, exc)
    else:
        log.info("Welcome email queued for %s", user.email)

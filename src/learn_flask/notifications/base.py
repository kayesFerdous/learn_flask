"""The contract every email sender has to satisfy.

This file is the Strategy pattern's "interface". Everything that can send an
email implements EmailSender, and the rest of the app only ever sees this type.
Swapping Brevo for SendGrid, for the console, or for nothing at all becomes a
change of one line in a factory -- no service, no route, no test has to know.

Note how small EmailSender is: one method. That is Interface Segregation. A fat
interface with send/retry/format/log would force NullSender to implement four
methods just to do nothing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """One message, ready to send.

    frozen=True makes it read-only, so nothing can quietly rewrite the recipient
    after the message has been built. It is also plain data with no open network
    connection inside it, which matters: rq has to pickle this object to hand it
    to the background worker.
    """

    to_email: str
    to_name: str
    subject: str
    text: str
    html: str


class EmailSender(ABC):
    """Send one email.

    Implementations MUST NOT raise. A failed welcome email is not a reason to
    fail a signup that already succeeded -- the user's account exists either
    way. Log the problem and return.
    """

    @abstractmethod
    def send(self, email: Email) -> None: ...

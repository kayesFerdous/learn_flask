"""Send in the background instead of during the web request.

This is the Decorator pattern, the real GoF one -- not a Python @decorator.
QueuedSender *is* an EmailSender and it *has* an EmailSender. It adds one
behaviour (do it later, somewhere else) and forwards everything else.

    BrevoSender()                  -> sends during the request, slow signup
    QueuedSender(BrevoSender())    -> signup returns immediately

The important part: nothing else in the app changes. UserService still calls
`self.email.send(...)` and has no idea whether the work happens now or in a
worker process two containers away.
"""

import logging

from learn_flask.notifications.base import Email, EmailSender

log = logging.getLogger(__name__)


def deliver(sender: EmailSender, email: Email) -> None:
    """The function rq actually runs, inside the worker process.

    rq pickles `sender` and `email` and unpickles them in the worker. That works
    because both are plain data -- see the note in BrevoSender.__init__. The
    worker has no Flask app and does not need one: everything it needs came
    along in the job.
    """
    sender.send(email)


class QueuedSender(EmailSender):
    def __init__(self, inner: EmailSender, queue):
        self._inner = inner
        self._queue = queue

    def send(self, email: Email) -> None:
        try:
            self._queue.enqueue(deliver, self._inner, email)
        except Exception as exc:
            # Redis being down must not fail a signup that already worked. Fall
            # back to sending inline -- slower, but the email still goes out.
            log.warning("Could not queue the email to %s: %s", email.to_email, exc)
            self._inner.send(email)

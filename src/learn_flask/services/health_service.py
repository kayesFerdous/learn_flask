"""Is this app actually able to do its job right now?

One method, in its own service, for one reason: the rule that resources/ never
touches the database has no exceptions. A `SELECT 1` in a route would be a small
crack, and small cracks are how a layer stops meaning anything.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)


class HealthService:
    def __init__(self, session):
        self.session = session

    def database_is_reachable(self):
        """Actually talk to the database instead of assuming it is there.

        A health check that only proves the web server answered is close to
        useless -- gunicorn will happily reply 200 while Postgres is down and
        every real request is failing.
        """
        try:
            self.session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            # The session is left in a broken state after a failed statement.
            # Without this rollback the NEXT request on this connection fails
            # too, and the health check becomes the thing causing the outage.
            self.session.rollback()
            log.warning("Health check could not reach the database: %s", exc)
            return False
        return True

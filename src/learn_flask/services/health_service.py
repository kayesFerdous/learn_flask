import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)


class HealthService:
    def __init__(self, session):
        self.session = session

    def database_is_reachable(self):
        try:
            self.session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            # Without this rollback the session stays broken and the next
            # request fails too -- the health check becomes the outage.
            self.session.rollback()
            log.warning("Health check could not reach the database: %s", exc)
            return False
        return True

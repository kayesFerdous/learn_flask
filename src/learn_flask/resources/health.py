"""GET /health -- can this app serve traffic right now?

Deliberately unauthenticated. Whatever is checking this (docker compose, Render,
a load balancer) has no token and never will.
"""

from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.errors import ServiceUnavailableError
from learn_flask.resources import services
from learn_flask.schemas import HealthSchema

health_blp = Blueprint(
    "Health", "health", description="Liveness and readiness for orchestrators"
)


@health_blp.route("/health")
class Health(MethodView):
    @health_blp.response(200, HealthSchema)
    @health_blp.alt_response(503, description="The database is not reachable.")
    def get(self):
        if not services().health.database_is_reachable():
            # Raising rather than returning a 503 by hand, so this endpoint
            # produces exactly the same error shape as every other route.
            raise ServiceUnavailableError("The database is not reachable.")

        return {"status": "ok", "database": "ok"}

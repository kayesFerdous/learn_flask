from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.errors import ServiceUnavailableError
from learn_flask.resources import services
from learn_flask.schemas import HealthSchema

health_blp = Blueprint(
    "Health", "health", description="Liveness and readiness for orchestrators"
)


# Unauthenticated on purpose: whatever polls this has no token.
@health_blp.route("/health")
class Health(MethodView):
    @health_blp.response(200, HealthSchema)
    @health_blp.alt_response(503, description="The database is not reachable.")
    def get(self):
        if not services().health.database_is_reachable():
            raise ServiceUnavailableError("The database is not reachable.")
        return {"status": "ok", "database": "ok"}

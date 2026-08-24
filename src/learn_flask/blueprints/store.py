from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.blueprints import get_store_or_404, stores
from learn_flask.schemas import StoreSchema, MessageSchema


store_blp = Blueprint(
    "Stores", "stores", url_prefix="/stores", description="Operations on stores"
)

@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.response(200, StoreSchema(many=True))
    def get(self):
        return [{"id": store_id, "items": items} for store_id, items in stores.items()]

    @store_blp.response(201, StoreSchema)
    def post(self):
        store_id = max(stores) + 1 if stores else 1
        stores[store_id] = []
        return {"id": store_id, "items": []}


@store_blp.route("/<int:store_id>")
class Store(MethodView):
    @store_blp.response(200, StoreSchema)
    def get(self, store_id):
        return {"id": store_id, "items": get_store_or_404(store_id)}

    @store_blp.response(200, MessageSchema)
    def delete(self, store_id):
        get_store_or_404(store_id)
        del stores[store_id]
        return {"message": f"Store {store_id} deleted."}

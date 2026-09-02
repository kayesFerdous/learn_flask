from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.resources import services
from learn_flask.schemas import MessageSchema, StoreSchema, StoreUpdateSchema

store_blp = Blueprint(
    "Stores", "stores", url_prefix="/stores", description="Operations on stores"
)


@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.response(200, StoreSchema(many=True))
    def get(self):
        return services().stores.list_all()

    @store_blp.arguments(StoreSchema)
    @store_blp.response(201, StoreSchema)
    def post(self, store_data):
        return services().stores.create(store_data)


@store_blp.route("/<int:store_id>")
class Store(MethodView):
    @store_blp.response(200, StoreSchema)
    def get(self, store_id):
        return services().stores.get(store_id)

    @store_blp.arguments(StoreUpdateSchema)
    @store_blp.response(200, StoreSchema)
    def patch(self, store_data, store_id):
        return services().stores.update(store_id, store_data)

    @store_blp.response(200, MessageSchema)
    def delete(self, store_id):
        services().stores.delete(store_id)
        return {"message": f"Store {store_id} deleted."}

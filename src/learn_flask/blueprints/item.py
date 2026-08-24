from uuid import uuid4
from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.blueprints import get_item_or_404, get_store_or_404, stores
from learn_flask.schemas import ItemQuerySchema, ItemSchema, ItemUpdateSchema, MessageSchema


item_blp = Blueprint(
    "Items", "items", url_prefix="/stores", description="Operations on items in a store"
)

@item_blp.route("/<int:store_id>/items")
class ItemList(MethodView):
    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters, store_id):
        store = get_store_or_404(store_id)

        return [
            item
            for item in store
            if all(item.get(key) == value for key, value in filters.items())
        ]

    @item_blp.arguments(ItemSchema)
    @item_blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        store = get_store_or_404(store_id)

        item = {**item_data, "id": str(uuid4())}
        store.append(item)
        return item


@item_blp.route("/<int:store_id>/items/<item_id>")
class Item(MethodView):
    @item_blp.response(200, ItemSchema)
    def get(self, store_id, item_id):
        return get_item_or_404(store_id, item_id)

    @item_blp.arguments(ItemUpdateSchema)
    @item_blp.response(200, ItemSchema)
    def patch(self, item_data, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        item.update(item_data)
        return item

    @item_blp.response(200, MessageSchema)
    def delete(self, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        stores[store_id].remove(item)
        return {"message": f"Item '{item_id}' deleted."}

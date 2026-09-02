from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.resources import services
from learn_flask.schemas import (
    ItemQuerySchema,
    ItemSchema,
    ItemSearchSchema,
    ItemUpdateSchema,
    MessageSchema,
)

item_blp = Blueprint(
    "Items",
    "items",
    description=(
        "Operations on items in a store. The item collections also answer "
        "QUERY (RFC 10008) for filters too complex for a query string. "
        "Swagger cannot draw those operations -- OpenAPI 3.1 has no QUERY -- "
        "so they are documented in the source."
    ),
)


@item_blp.route("/items")
class ItemsAcrossStores(MethodView):
    # Flask only auto-detects the eight classic verbs, so QUERY has to be
    # declared by hand or the route answers 405.
    methods = ["GET", "QUERY"]

    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters):
        return services().items.list_all(filters)

    @item_blp.arguments(ItemSearchSchema)
    @item_blp.response(200, ItemSchema(many=True))
    def query(self, filters):
        return services().items.search(filters)


@item_blp.route("/stores/<int:store_id>/items")
class ItemList(MethodView):
    methods = ["GET", "POST", "QUERY"]

    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters, store_id):
        return services().items.list_for_store(store_id, filters)

    @item_blp.arguments(ItemSearchSchema)
    @item_blp.response(200, ItemSchema(many=True))
    def query(self, filters, store_id):
        return services().items.search(filters, store_id=store_id)

    @item_blp.arguments(ItemSchema)
    @item_blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        return services().items.create(store_id, item_data)


@item_blp.route("/stores/<int:store_id>/items/<uuid:item_id>")
class Item(MethodView):
    @item_blp.response(200, ItemSchema)
    def get(self, store_id, item_id):
        return services().items.get(item_id, store_id)

    @item_blp.arguments(ItemUpdateSchema)
    @item_blp.response(200, ItemSchema)
    def patch(self, item_data, store_id, item_id):
        return services().items.update(item_id, store_id, item_data)

    @item_blp.response(200, MessageSchema)
    def delete(self, store_id, item_id):
        services().items.delete(item_id, store_id)
        return {"message": f"Item '{item_id}' deleted."}

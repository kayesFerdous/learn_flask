from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.extensions import db
from learn_flask.blueprints import get_item_or_404, get_store_or_404
from learn_flask.models import ItemModel
from learn_flask.schemas import (
    ItemQuerySchema,
    ItemSchema,
    ItemUpdateSchema,
    MessageSchema,
)


item_blp = Blueprint(
    "Items", "items", url_prefix="/stores", description="Operations on items in a store"
)


@item_blp.route("/<int:store_id>/items")
class ItemList(MethodView):
    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters, store_id):
        store = get_store_or_404(store_id)
        return store.items.filter_by(**filters).all()

    @item_blp.arguments(ItemSchema)
    @item_blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        get_store_or_404(store_id)
        item = ItemModel(**item_data, store_id=store_id)
        db.session.add(item)
        db.session.commit()
        return item


@item_blp.route("/<int:store_id>/items/<uuid:item_id>")
class Item(MethodView):
    @item_blp.response(200, ItemSchema)
    def get(self, store_id, item_id):
        return get_item_or_404(store_id, item_id)

    @item_blp.arguments(ItemUpdateSchema)
    @item_blp.response(200, ItemSchema)
    def patch(self, item_data, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        for field, value in item_data.items():
            setattr(item, field, value)
        db.session.commit()
        return item

    @item_blp.response(200, MessageSchema)
    def delete(self, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Item '{item_id}' deleted."}

from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.blueprints import get_item_or_404, get_store_or_404
from learn_flask.extensions import db
from learn_flask.models import ItemModel, TagModel
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


def search_items(stmt, filters):
    """Narrow a select() with the filters from an ItemSearchSchema body."""
    if "name_contains" in filters:
        stmt = stmt.where(ItemModel.name.ilike(f"%{filters['name_contains']}%"))
    if "min_price" in filters:
        stmt = stmt.where(ItemModel.price >= filters["min_price"])
    if "max_price" in filters:
        stmt = stmt.where(ItemModel.price <= filters["max_price"])
    if "tags" in filters:
        # .any() becomes an EXISTS subquery, so an item is returned once even
        # when several of its tags match -- a join here would duplicate rows.
        stmt = stmt.where(ItemModel.tags.any(TagModel.name.in_(filters["tags"])))
    return stmt


@item_blp.route("/items")
class ItemsAcrossStores(MethodView):
    # Flask only auto-detects the eight classic verbs, so QUERY has to be
    # declared by hand or the route answers 405.
    methods = ["GET", "QUERY"]

    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters):
        return db.session.scalars(db.select(ItemModel).filter_by(**filters)).all()

    @item_blp.arguments(ItemSearchSchema)
    @item_blp.response(200, ItemSchema(many=True))
    def query(self, filters):
        # QUERY is safe and idempotent like GET -- it only reads. Use POST if
        # you ever need this route to change something.
        return db.session.scalars(search_items(db.select(ItemModel), filters)).all()


@item_blp.route("/stores/<int:store_id>/items")
class ItemList(MethodView):
    methods = ["GET", "POST", "QUERY"]

    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters, store_id):
        store = get_store_or_404(store_id)
        return store.items.filter_by(**filters).all()

    @item_blp.arguments(ItemSearchSchema)
    @item_blp.response(200, ItemSchema(many=True))
    def query(self, filters, store_id):
        get_store_or_404(store_id)
        stmt = search_items(
            db.select(ItemModel).where(ItemModel.store_id == store_id), filters
        )
        return db.session.scalars(stmt).all()

    @item_blp.arguments(ItemSchema)
    @item_blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        get_store_or_404(store_id)
        item = ItemModel(**item_data, store_id=store_id)
        db.session.add(item)
        db.session.commit()
        return item


@item_blp.route("/stores/<int:store_id>/items/<uuid:item_id>")
class Item(MethodView):
    @item_blp.response(200, ItemSchema)
    def get(self, store_id, item_id):
        return get_item_or_404(item_id, store_id)

    @item_blp.arguments(ItemUpdateSchema)
    @item_blp.response(200, ItemSchema)
    def patch(self, item_data, store_id, item_id):
        item = get_item_or_404(item_id, store_id)
        for field, value in item_data.items():
            setattr(item, field, value)
        db.session.commit()
        return item

    @item_blp.response(200, MessageSchema)
    def delete(self, store_id, item_id):
        item = get_item_or_404(item_id, store_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Item '{item_id}' deleted."}

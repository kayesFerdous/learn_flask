from flask_smorest import abort

from learn_flask.extensions import db
from learn_flask.models import ItemModel, StoreModel, TagModel


def get_store_or_404(store_id):
    store = db.session.get(StoreModel, store_id)
    if store is None:
        abort(404, message=f"Store {store_id} not found.")
    return store


def get_item_or_404(item_id, store_id=None):
    item = db.session.get(ItemModel, item_id)
    if item is None or (store_id is not None and item.store_id != store_id):
        where = f" in store {store_id}" if store_id is not None else ""
        abort(404, message=f"Item '{item_id}' not found{where}.")
    return item


def get_tag_or_404(tag_id, store_id=None):
    tag = db.session.get(TagModel, tag_id)
    if tag is None or (store_id is not None and tag.store_id != store_id):
        where = f" in store {store_id}" if store_id is not None else ""
        abort(404, message=f"Tag '{tag_id}' not found{where}.")
    return tag


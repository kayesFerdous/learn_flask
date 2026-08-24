from flask_smorest import abort

from learn_flask.extensions import db
from learn_flask.models import ItemModel, StoreModel


def get_store_or_404(store_id):
    store = db.session.get(StoreModel, store_id)
    if store is None:
        abort(404, message=f"Store {store_id} not found.")
    return store


def get_item_or_404(store_id, item_id):
    item = db.session.get(ItemModel, item_id)
    if item is None or item.store_id != store_id:
        abort(404, message=f"Item '{item_id}' not found in store {store_id}.")
    return item

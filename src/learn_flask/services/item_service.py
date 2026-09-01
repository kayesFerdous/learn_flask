"""Business rules for items, including the QUERY search."""

from sqlalchemy import select

from learn_flask.errors import NotFoundError
from learn_flask.models import ItemModel, TagModel


class ItemService:
    def __init__(self, session, stores):
        self.session = session
        # A service is allowed to lean on another service. Item lookups have to
        # check the store exists, and StoreService already knows how to do that
        # and how to raise the right error -- so do not write it twice.
        self.stores = stores

    # --- reading ----------------------------------------------------------

    def get(self, item_id, store_id=None):
        item = self.session.get(ItemModel, item_id)
        if item is None or (store_id is not None and item.store_id != store_id):
            where = f" in store {store_id}" if store_id is not None else ""
            raise NotFoundError(f"Item '{item_id}' not found{where}.")
        return item

    def list_all(self, filters):
        return self.session.scalars(select(ItemModel).filter_by(**filters)).all()

    def list_for_store(self, store_id, filters):
        store = self.stores.get(store_id)
        return store.items.filter_by(**filters).all()

    def search(self, filters, store_id=None):
        """The body of a QUERY request: filters that combine."""
        stmt = select(ItemModel)
        if store_id is not None:
            self.stores.get(store_id)
            stmt = stmt.where(ItemModel.store_id == store_id)
        return self.session.scalars(self._apply_filters(stmt, filters)).all()

    @staticmethod
    def _apply_filters(stmt, filters):
        if "name_contains" in filters:
            stmt = stmt.where(ItemModel.name.ilike(f"%{filters['name_contains']}%"))
        if "min_price" in filters:
            stmt = stmt.where(ItemModel.price >= filters["min_price"])
        if "max_price" in filters:
            stmt = stmt.where(ItemModel.price <= filters["max_price"])
        if "tags" in filters:
            # .any() becomes an EXISTS subquery, so an item is returned once
            # even when several of its tags match -- a join would duplicate rows.
            stmt = stmt.where(ItemModel.tags.any(TagModel.name.in_(filters["tags"])))
        return stmt

    # --- writing ----------------------------------------------------------

    def create(self, store_id, data):
        self.stores.get(store_id)
        item = ItemModel(**data, store_id=store_id)
        self.session.add(item)
        self.session.commit()
        return item

    def update(self, item_id, store_id, data):
        item = self.get(item_id, store_id)
        for field, value in data.items():
            setattr(item, field, value)
        self.session.commit()
        return item

    def delete(self, item_id, store_id):
        item = self.get(item_id, store_id)
        self.session.delete(item)
        self.session.commit()

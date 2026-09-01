from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from learn_flask.errors import BusinessRuleError, ConflictError, NotFoundError
from learn_flask.models import TagModel

TAKEN = "This store already has a tag with that name."


class TagService:
    def __init__(self, session, stores, items):
        self.session = session
        self.stores = stores
        self.items = items

    def get(self, tag_id, store_id=None):
        tag = self.session.get(TagModel, tag_id)
        if tag is None or (store_id is not None and tag.store_id != store_id):
            where = f" in store {store_id}" if store_id is not None else ""
            raise NotFoundError(f"Tag '{tag_id}' not found{where}.")
        return tag

    def list_all(self):
        return self.session.scalars(select(TagModel)).all()

    def list_for_store(self, store_id):
        return self.stores.get(store_id).tags.all()

    def create(self, store_id, data):
        self.stores.get(store_id)
        tag = TagModel(**data, store_id=store_id)
        self.session.add(tag)
        self._commit()
        return tag

    def update(self, tag_id, data):
        tag = self.get(tag_id)
        for field, value in data.items():
            setattr(tag, field, value)
        self._commit()
        return tag

    def delete(self, tag_id):
        tag = self.get(tag_id)
        if tag.items:
            raise BusinessRuleError(
                "Tag is linked to items. Unlink them before deleting the tag."
            )
        self.session.delete(tag)
        self.session.commit()

    def link_to_item(self, item_id, tag_id):
        item = self.items.get(item_id)
        tag = self.get(tag_id)

        if item.store_id != tag.store_id:
            raise BusinessRuleError("Item and tag must belong to the same store.")

        if tag not in item.tags:
            item.tags.append(tag)
            self.session.commit()
        return tag

    def unlink_from_item(self, item_id, tag_id):
        item = self.items.get(item_id)
        tag = self.get(tag_id)

        if tag not in item.tags:
            raise NotFoundError(f"Tag '{tag_id}' is not linked to item '{item_id}'.")

        item.tags.remove(tag)
        self.session.commit()
        return item, tag

    def _commit(self):
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError(TAKEN) from None

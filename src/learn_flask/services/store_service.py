"""Business rules for stores. No Flask anywhere in this file -- on purpose."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from learn_flask.errors import ConflictError, NotFoundError
from learn_flask.models import StoreModel


class StoreService:
    def __init__(self, session):
        # The session arrives from outside instead of being imported. That is
        # dependency injection, and it is why this class has no idea whether it
        # is running in a web request, a test, or a script.
        self.session = session

    def get(self, store_id):
        store = self.session.get(StoreModel, store_id)
        if store is None:
            raise NotFoundError(f"Store {store_id} not found.")
        return store

    def list_all(self):
        return self.session.scalars(select(StoreModel)).all()

    def create(self, data):
        store = StoreModel(**data)
        try:
            self.session.add(store)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError("A store with this name already exists.") from None
        return store

    def update(self, store_id, data):
        store = self.get(store_id)
        for field, value in data.items():
            setattr(store, field, value)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError("A store with this name already exists.") from None
        return store

    def delete(self, store_id):
        store = self.get(store_id)
        self.session.delete(store)
        self.session.commit()

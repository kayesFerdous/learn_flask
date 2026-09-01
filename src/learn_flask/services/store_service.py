from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from learn_flask.errors import ConflictError, NotFoundError
from learn_flask.models import StoreModel

TAKEN = "A store with this name already exists."


class StoreService:
    def __init__(self, session):
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
        self.session.add(store)
        self._commit()
        return store

    def update(self, store_id, data):
        store = self.get(store_id)
        for field, value in data.items():
            setattr(store, field, value)
        self._commit()
        return store

    def delete(self, store_id):
        self.session.delete(self.get(store_id))
        self.session.commit()

    def _commit(self):
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError(TAKEN) from None

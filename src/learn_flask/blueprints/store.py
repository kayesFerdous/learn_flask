from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from learn_flask.extensions import db
from learn_flask.blueprints import get_store_or_404
from learn_flask.models import StoreModel
from learn_flask.schemas import MessageSchema, StoreSchema


store_blp = Blueprint(
    "Stores", "stores", url_prefix="/stores", description="Operations on stores"
)


@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.response(200, StoreSchema(many=True))
    def get(self):
        return db.session.scalars(db.select(StoreModel)).all()

    @store_blp.arguments(StoreSchema)
    @store_blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(400, message="A store with this name already exists.")

        return store


@store_blp.route("/<int:store_id>")
class Store(MethodView):
    @store_blp.response(200, StoreSchema)
    def get(self, store_id):
        return get_store_or_404(store_id)

    @store_blp.response(200, MessageSchema)
    def delete(self, store_id):
        store = get_store_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": f"Store {store_id} deleted."}

import uuid

from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields


class ItemSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)


class ItemUpdateSchema(Schema):
    name = fields.Str()
    price = fields.Float()


class ItemQuerySchema(Schema):
    name = fields.Str()
    price = fields.Float()


class StoreSchema(Schema):
    id = fields.Int(dump_only=True)
    items = fields.List(fields.Nested(ItemSchema), dump_only=True)


class MessageSchema(Schema):
    message = fields.Str()


stores = {
    1: [
        {
            "id": "ae030ebe-ce0b-4557-89b0-1ec110a3d450",
            "name": "Wireless Mouse",
            "price": 850,
        },
        {
            "id": "087ca864-2be4-457e-80bb-fe8f1251384e",
            "name": "Mechanical Keyboard",
            "price": 3200,
        },
        {"id": "f0c6cb6f-3481-4014-a49c-936dfa37d888", "name": "Webcam", "price": 2500},
    ],
    2: [
        {
            "id": "34872fff-f147-49de-82db-bc12fe98c8d7",
            "name": "USB-C Cable",
            "price": 450,
        },
        {
            "id": "657e7f1d-1c0e-43c7-9402-302dd6343d5d",
            "name": "Laptop Stand",
            "price": 1500,
        },
        {
            "id": "77e23a71-3bde-4557-8059-2c0927a4b3ff",
            "name": "Power Bank",
            "price": 1800,
        },
    ],
    3: [
        {
            "id": "c9571ce0-693e-4150-ad84-40699df85181",
            "name": "Bluetooth Speaker",
            "price": 2800,
        },
        {
            "id": "4f1b7312-c8fa-458d-a6b1-c0c79b1ea606",
            "name": "Gaming Headset",
            "price": 4200,
        },
    ],
}


def get_store_or_404(store_id):
    if store_id not in stores:
        abort(404, message=f"Store {store_id} not found.")
    return stores[store_id]


def get_item_or_404(store_id, item_id):
    store = get_store_or_404(store_id)
    item = next((i for i in store if i["id"] == item_id), None)
    if item is None:
        abort(404, message=f"Item '{item_id}' not found in store {store_id}.")
    return item


store_blp = Blueprint(
    "Stores", "stores", url_prefix="/stores", description="Operations on stores"
)

item_blp = Blueprint(
    "Items", "items", url_prefix="/stores", description="Operations on items in a store"
)


@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.response(200, StoreSchema(many=True))
    def get(self):
        return [{"id": store_id, "items": items} for store_id, items in stores.items()]

    @store_blp.response(201, StoreSchema)
    def post(self):
        store_id = max(stores) + 1 if stores else 1
        stores[store_id] = []
        return {"id": store_id, "items": []}


@store_blp.route("/<int:store_id>")
class Store(MethodView):
    @store_blp.response(200, StoreSchema)
    def get(self, store_id):
        return {"id": store_id, "items": get_store_or_404(store_id)}

    @store_blp.response(200, MessageSchema)
    def delete(self, store_id):
        get_store_or_404(store_id)
        del stores[store_id]
        return {"message": f"Store {store_id} deleted."}


@item_blp.route("/<int:store_id>/items")
class ItemList(MethodView):
    @item_blp.arguments(ItemQuerySchema, location="query")
    @item_blp.response(200, ItemSchema(many=True))
    def get(self, filters, store_id):
        store = get_store_or_404(store_id)

        return [
            item
            for item in store
            if all(item.get(key) == value for key, value in filters.items())
        ]

    @item_blp.arguments(ItemSchema)
    @item_blp.response(201, ItemSchema)
    def post(self, item_data, store_id):
        store = get_store_or_404(store_id)

        item = {**item_data, "id": str(uuid.uuid4())}
        store.append(item)
        return item


@item_blp.route("/<int:store_id>/items/<item_id>")
class Item(MethodView):
    @item_blp.response(200, ItemSchema)
    def get(self, store_id, item_id):
        return get_item_or_404(store_id, item_id)

    @item_blp.arguments(ItemUpdateSchema)
    @item_blp.response(200, ItemSchema)
    def patch(self, item_data, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        item.update(item_data)
        return item

    @item_blp.response(200, MessageSchema)
    def delete(self, store_id, item_id):
        item = get_item_or_404(store_id, item_id)
        stores[store_id].remove(item)
        return {"message": f"Item '{item_id}' deleted."}


app = Flask(__name__)

app.config["API_TITLE"] = "Store API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.1.0"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "openapi.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
app.config["PROPAGATE_EXCEPTIONS"] = True

api = Api(app)
api.register_blueprint(store_blp)
api.register_blueprint(item_blp)


def main():
    app.run(host="0.0.0.0", port=3000, debug=True)

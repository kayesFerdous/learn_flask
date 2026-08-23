import uuid

from flask import Flask, request
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
# from marshmallow import Schema, fields


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

NUMERIC_KEYS = ["price"]


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


def to_numbers(data):
    for key in NUMERIC_KEYS:
        if key in data:
            data[key] = int(data[key])
    return data


store_blp = Blueprint(
    "Stores", "stores", url_prefix="/stores", description="Operations on stores"
)

item_blp = Blueprint(
    "Items", "items", url_prefix="/stores", description="Operations on items in a store"
)


@store_blp.route("/")
class StoreList(MethodView):
    def get(self):
        return stores

    def post(self):
        store_id = max(stores) + 1 if stores else 1
        stores[store_id] = []
        return {"id": store_id, "items": []}, 201


@store_blp.route("/<int:store_id>")
class Store(MethodView):
    def get(self, store_id):
        return {"id": store_id, "items": get_store_or_404(store_id)}

    def delete(self, store_id):
        get_store_or_404(store_id)
        del stores[store_id]
        return {"message": f"Store {store_id} deleted."}


@item_blp.route("/<int:store_id>/items")
class ItemList(MethodView):
    def get(self, store_id):
        store = get_store_or_404(store_id)
        filters = to_numbers(request.args.to_dict())

        return [
            item
            for item in store
            if all(item.get(key) == value for key, value in filters.items())
        ]

    def post(self, store_id):
        store = get_store_or_404(store_id)

        data = request.get_json(silent=True)
        if data is None:
            abort(400, message="Request body must be JSON.")

        missing = [key for key in ("name", "price") if key not in data]
        if missing:
            abort(400, message=f"Missing fields: {', '.join(missing)}.")

        item = to_numbers({"name": data["name"], "price": data["price"]})
        item["id"] = str(uuid.uuid4())

        store.append(item)
        return item, 201


@item_blp.route("/<int:store_id>/items/<item_id>")
class Item(MethodView):
    def get(self, store_id, item_id):
        return get_item_or_404(store_id, item_id)

    def patch(self, store_id, item_id):
        item = get_item_or_404(store_id, item_id)

        data = request.get_json(silent=True)
        if data is None:
            abort(400, message="Request body must be JSON.")

        # The id identifies the item; a client must not be able to change it.
        data.pop("id", None)

        item.update(to_numbers(data))
        return item

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

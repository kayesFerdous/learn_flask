from flask import Flask, jsonify, request

stores = {
    1: [
        {"name": "Wireless Mouse", "price": 850},
        {"name": "Mechanical Keyboard", "price": 3200},
        {"name": "Webcam", "price": 2500},
    ],
    2: [
        {"name": "USB-C Cable", "price": 450},
        {"name": "Laptop Stand", "price": 1500},
        {"name": "Power Bank", "price": 1800},
    ],
    3: [
        {"name": "Bluetooth Speaker", "price": 2800},
        {"name": "Gaming Headset", "price": 4200},
    ],
}

app = Flask(__name__)

NUMERIC_KEYS = ["price"]


def find_item(store_id, item_name):
    return next((i for i in stores[store_id] if i["name"] == item_name), None)


def to_numbers(data):
    for key in NUMERIC_KEYS:
        if key in data:
            data[key] = int(data[key])
    return data


@app.get("/")
def index():
    return jsonify({"message": "Store API", "stores": len(stores)})


@app.get("/stores")
def list_stores():
    return jsonify(stores)


@app.post("/stores")
def create_store():
    new_id = max(stores) + 1 if stores else 1
    stores[new_id] = []
    return jsonify({"id": new_id, "items": []}), 201


@app.get("/stores/<int:store_id>")
def get_store(store_id):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    return jsonify({"id": store_id, "items": stores[store_id]})


@app.delete("/stores/<int:store_id>")
def delete_store(store_id):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    del stores[store_id]
    return jsonify({"message": f"store {store_id} deleted"})


@app.get("/stores/<int:store_id>/items")
def list_items(store_id):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    filters = to_numbers(request.args.to_dict())

    matched = [
        i
        for i in stores[store_id]
        if all(i.get(key) == value for key, value in filters.items())
    ]

    return jsonify(matched)


@app.post("/stores/<int:store_id>/items")
def create_item(store_id):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "body must be JSON"}), 400

    missing = [key for key in ("name", "price") if key not in data]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400

    if find_item(store_id, data["name"]):
        return jsonify({"error": f"item '{data['name']}' already exists"}), 409

    item = to_numbers({"name": data["name"], "price": data["price"]})
    stores[store_id].append(item)

    return jsonify(item), 201


@app.get("/stores/<int:store_id>/items/<item_name>")
def get_item(store_id, item_name):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    item = find_item(store_id, item_name)
    if item is None:
        return jsonify({"error": f"item '{item_name}' not found"}), 404

    return jsonify(item)


@app.patch("/stores/<int:store_id>/items/<item_name>")
def update_item(store_id, item_name):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    item = find_item(store_id, item_name)
    if item is None:
        return jsonify({"error": f"item '{item_name}' not found"}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "body must be JSON"}), 400

    item.update(to_numbers(data))
    return jsonify(item)


@app.delete("/stores/<int:store_id>/items/<item_name>")
def delete_item(store_id, item_name):
    if store_id not in stores:
        return jsonify({"error": f"store {store_id} not found"}), 404

    item = find_item(store_id, item_name)
    if item is None:
        return jsonify({"error": f"item '{item_name}' not found"}), 404

    stores[store_id].remove(item)
    return jsonify({"message": f"item '{item_name}' deleted"})


def main():
    app.run(host="0.0.0.0", port=3000, debug=True)

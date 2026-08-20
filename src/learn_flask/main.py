from flask import Flask, jsonify, request


products = [
    {
        "id": 1,
        "name": "Wireless Mouse",
        "price": 850,
        "category": "Electronics",
        "stock": 45,
    },
    {
        "id": 2,
        "name": "Mechanical Keyboard",
        "price": 3200,
        "category": "Electronics",
        "stock": 20,
    },
    {
        "id": 3,
        "name": "USB-C Cable",
        "price": 450,
        "category": "Accessories",
        "stock": 80,
    },
    {
        "id": 4,
        "name": "Laptop Stand",
        "price": 1500,
        "category": "Accessories",
        "stock": 30,
    },
    {
        "id": 5,
        "name": "Bluetooth Speaker",
        "price": 2800,
        "category": "Audio",
        "stock": 15,
    },
    {
        "id": 6,
        "name": "Gaming Headset",
        "price": 4200,
        "category": "Audio",
        "stock": 12,
    },
    {"id": 7, "name": "Webcam", "price": 2500, "category": "Electronics", "stock": 18},
    {
        "id": 8,
        "name": "Power Bank",
        "price": 1800,
        "category": "Accessories",
        "stock": 35,
    },
    {"id": 9, "name": "Desk Lamp", "price": 1200, "category": "Home", "stock": 25},
    {
        "id": 10,
        "name": "Notebook",
        "price": 250,
        "category": "Stationery",
        "stock": 100,
    },
]

app = Flask(__name__)


@app.get("/")
def index():
    return "This is the index route"


@app.get("/products/<int:product_id>")
def get_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)

    if product:
        return jsonify(product)
    else:
        return f"Product id: {product_id} not found"


@app.get("/products")
def search_product():
    args = request.args.to_dict()

    numeric_keys = ["id", "price", "stock"]

    for key in args:
        if key in numeric_keys:
            args[key] = int(args[key])

    matched = [
        p for p in products if all([p.get(key) == value for key, value in args.items()])
    ]

    return jsonify(matched)


@app.delete("/products/<int:product_id>")
def delete_product(product_id):

    global products

    products = [p for p in products if p["id"] != product_id]

    return f"product id {product_id} has been deleted"


@app.patch("/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json()

    numeric_keys = ["id", "price", "stock"]

    for key in data:
        if key in numeric_keys:
            data[key] = int(data[key])

    global products

    for p in products:
        if p["id"] == product_id:
            for key, value in data.items():
                p[key] = value
            return p

    return "nothing found", 404


def main():
    app.run(host="0.0.0.0", port=3000, debug=True)

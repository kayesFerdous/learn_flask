from flask_smorest import abort


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

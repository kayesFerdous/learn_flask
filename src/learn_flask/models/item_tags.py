from learn_flask.extensions import db

items_tags = db.Table(
    "items_tags",
    db.Column("item_id", db.Uuid, db.ForeignKey("items.id"), primary_key=True),
    db.Column("tag_id", db.Uuid, db.ForeignKey("tags.id"), primary_key=True),
)

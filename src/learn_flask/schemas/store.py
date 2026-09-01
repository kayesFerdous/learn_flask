from marshmallow import fields

from learn_flask.schemas.plain import PlainItemSchema, PlainStoreSchema, PlainTagSchema


class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)

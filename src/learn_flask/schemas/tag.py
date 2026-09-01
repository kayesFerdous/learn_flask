from marshmallow import Schema, fields

from learn_flask.schemas.plain import PlainItemSchema, PlainStoreSchema, PlainTagSchema


class TagSchema(PlainTagSchema):
    store = fields.Nested(PlainStoreSchema(), dump_only=True)
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)


class TagAndItemSchema(Schema):
    message = fields.Str()
    item = fields.Nested(PlainItemSchema(), dump_only=True)
    tag = fields.Nested(PlainTagSchema(), dump_only=True)

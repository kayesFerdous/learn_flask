from marshmallow import Schema, fields, validate

from learn_flask.schemas.plain import PlainItemSchema, PlainStoreSchema, PlainTagSchema


class TagSchema(PlainTagSchema):
    store = fields.Nested(PlainStoreSchema(), dump_only=True)
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)


class TagAndItemSchema(Schema):
    message = fields.Str()
    item = fields.Nested(PlainItemSchema(), dump_only=True)
    tag = fields.Nested(PlainTagSchema(), dump_only=True)


class TagUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1))

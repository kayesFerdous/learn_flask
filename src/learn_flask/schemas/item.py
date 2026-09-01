from marshmallow import Schema, fields, validate

from learn_flask.schemas.plain import PlainItemSchema, PlainStoreSchema, PlainTagSchema


class ItemSchema(PlainItemSchema):
    store = fields.Nested(PlainStoreSchema(), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)


class ItemUpdateSchema(Schema):
    name = fields.Str()
    description = fields.Str()
    price = fields.Float(validate=validate.Range(min=0))


class ItemQuerySchema(Schema):
    name = fields.Str()
    price = fields.Float()

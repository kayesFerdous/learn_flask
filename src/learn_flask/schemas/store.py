from marshmallow import Schema, fields, validate

from learn_flask.schemas.plain import PlainItemSchema, PlainStoreSchema, PlainTagSchema


class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)


class StoreUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1))

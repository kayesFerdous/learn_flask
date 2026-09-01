from marshmallow import Schema, fields


class PlainItemSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    # The column is NOT NULL, so leaving this out of the schema turned a missing
    # description into a 500 from the database instead of a 422 from marshmallow.
    description = fields.Str(required=True)
    price = fields.Float(required=True)


class PlainStoreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


class PlainTagSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)

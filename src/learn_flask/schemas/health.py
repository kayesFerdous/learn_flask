from marshmallow import Schema, fields


class HealthSchema(Schema):
    status = fields.Str(dump_only=True)
    database = fields.Str(dump_only=True)

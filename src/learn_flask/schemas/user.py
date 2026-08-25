from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=8)
    )


class UserLoginSchema(Schema):
    name = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class TokenSchema(Schema):
    access_token = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)

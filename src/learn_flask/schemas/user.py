from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    # The username the client picks. Unique in the database, so registering a
    # taken one is rejected with a message saying so.
    name = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    # fields.Email rejects anything that isn't shaped like an address.
    # fields.Str would happily accept "not-an-email".
    email = fields.Email(required=True, validate=validate.Length(min=1, max=80))
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=8)
    )


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class TokenSchema(Schema):
    access_token = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)

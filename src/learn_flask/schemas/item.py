from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)

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


class ItemSearchSchema(Schema):
    """Body of a QUERY request.

    ItemQuerySchema is exact-match only, because that is all a query string
    does comfortably. These filters combine, so they need a request body.
    """

    name_contains = fields.Str(validate=validate.Length(min=1))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    # An item matches if it carries any one of these tag names.
    tags = fields.List(fields.Str(validate=validate.Length(min=1)))

    @validates_schema
    def check_price_range(self, data, **kwargs):
        low, high = data.get("min_price"), data.get("max_price")
        if low is not None and high is not None and low > high:
            raise ValidationError(
                "min_price cannot be greater than max_price.", "min_price"
            )

from marshmallow import Schema, fields, validate
from decimal import ROUND_HALF_UP

class ProductSchema(Schema):
    id = fields.Str(dump_only=True)
    product_code = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(required=False, allow_none=True)
    price = fields.Decimal(
        required=True, 
        as_string=True, 
        validate=validate.Range(min=0),
        places=2,  # Explicitly round to 2 decimal places
        rounding=ROUND_HALF_UP # Use a standard rounding mode for currency
    )
    stock = fields.Int(required=True, validate=validate.Range(min=0))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

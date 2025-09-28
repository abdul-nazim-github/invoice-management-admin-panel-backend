from marshmallow import fields, validate
from decimal import ROUND_HALF_UP
from .base_schema import BaseSchema

class ProductSchema(BaseSchema): # Inherit from our new BaseSchema
    id = fields.Str(dump_only=True)
    product_code = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(required=False, allow_none=True)
    price = fields.Decimal(
        required=True, 
        validate=validate.Range(min=0),
        places=2,  # Still important for input validation
        rounding=ROUND_HALF_UP # Still important for input validation
    )
    stock = fields.Int(required=True, validate=validate.Range(min=0))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # The specific @post_dump method is no longer needed!
    # It's handled automatically by the parent BaseSchema.

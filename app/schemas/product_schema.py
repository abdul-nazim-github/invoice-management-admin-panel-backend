from marshmallow import Schema, fields, validate

class ProductSchema(Schema):
    id = fields.Str(dump_only=True)
    product_code = fields.Str(dump_only=True) # Changed from required=True
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(required=False, allow_none=True)
    price = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0))
    stock = fields.Int(required=True, validate=validate.Range(min=0))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

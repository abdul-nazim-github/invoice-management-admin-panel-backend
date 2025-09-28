from marshmallow import Schema, fields, validate, ValidationError

class ProductSchema(Schema):
    """
    Marshmallow schema for validating product data.
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, error="Product name must be at least 2 characters long.")
    )
    description = fields.Str(required=True)
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    stock = fields.Int(
        required=True,
        validate=validate.Range(min=0, error="Stock must be a non-negative integer.")
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

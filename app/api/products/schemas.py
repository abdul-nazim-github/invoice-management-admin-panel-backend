from marshmallow import Schema, fields, validate


# ------------------------
# Schema for creating a product
# ------------------------
class ProductCreateSchema(Schema):
    sku = fields.Str(                                 
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "SKU is required"},
    )
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={"required": "Product name is required"},
    )
    description = fields.Str(required=False, allow_none=True)

    unit_price = fields.Decimal(                       # ✅ fixed
        required=True,
        as_string=True,
        places=2,
        error_messages={"required": "Unit price is required"},
    )
    stock_quantity = fields.Int(                       # ✅ fixed
        required=False,
        load_default=0,
        validate=validate.Range(min=0, error="Stock cannot be negative"),
    )

    status = fields.Str(
        required=False,
        validate=validate.OneOf(["active", "inactive"]),
        load_default="active",
    )


# ------------------------
# Schema for updating a product
# ------------------------
class ProductUpdateSchema(Schema):
    sku = fields.Str(required=False, validate=validate.Length(max=50))   # ✅ fixed
    name = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False, allow_none=True)
    unit_price = fields.Decimal(required=False, as_string=True, places=2)   # ✅ fixed
    stock_quantity = fields.Int(                                           # ✅ fixed
        required=False, validate=validate.Range(min=0, error="Stock cannot be negative")
    )
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]))


# ------------------------
# Schema for bulk delete
# ------------------------
class ProductBulkDeleteSchema(Schema):
    ids = fields.List(
        fields.UUID(),
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "IDs are required"},
    )


# ------------------------
# Schema for query/filtering
# ------------------------
class ProductFilterSchema(Schema):
    q = fields.Str(required=False, allow_none=True)
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]), required=False)
    page = fields.Int(load_default=1)
    limit = fields.Int(load_default=10)

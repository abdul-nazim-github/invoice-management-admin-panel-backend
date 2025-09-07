import re
from marshmallow import Schema, ValidationError, fields, validate


# ------------------------
# Schema for creating a customer
# ------------------------
def validate_gst(value):
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, value):
        raise ValidationError("Invalid GST number")


class CustomerCreateSchema(Schema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "Name is required"},
    )
    email = fields.Email(
        required=False,
        allow_none=True,
        error_messages={"invalid": "Invalid email address"},
    )
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=7, max=15),
        error_messages={"invalid": "Invalid phone number"},
    )
    address = fields.Str(required=False, allow_none=True)
    gst_number = fields.Str(
        required=False,
        allow_none=True,
        validate=validate_gst,  # ✅ custom GST validation
    )
    status = fields.Str(
        required=False,
        validate=validate.OneOf(
            ["active", "inactive"], error="Status must be active or inactive"
        ),
        load_default="active",
    )


# ------------------------
# Schema for updating a customer
# ------------------------
class CustomerUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.Str(
        required=False, allow_none=True, validate=validate.Length(min=7, max=15)
    )
    address = fields.Str(required=False, allow_none=True)
    gst_number = fields.Str(required=False, allow_none=True)
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]))


# ------------------------
# Schema for bulk delete
# ------------------------
class CustomerBulkDeleteSchema(Schema):
    ids = fields.List(
        fields.UUID(),
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "IDs are required"},
    )


# ------------------------
# Schema for query/filtering (optional)
# ------------------------
class CustomerFilterSchema(Schema):
    q = fields.Str(required=False, allow_none=True)
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]), required=False)
    page = fields.Int(load_default=1)
    limit = fields.Int(load_default=10)

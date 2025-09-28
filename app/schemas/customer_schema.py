from marshmallow import Schema, fields

class CustomerSchema(Schema):
    """Schema for validating and serializing customer data."""
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, metadata={"description": "Customer's full name."})
    email = fields.Email(required=True, metadata={"description": "Unique email address."})
    phone = fields.Str(required=True, metadata={"description": "Contact phone number."})
    address = fields.Str(metadata={"description": "Physical address."})
    gst_number = fields.Str(metadata={"description": "GST identification number."})
    created_at = fields.DateTime(dump_only=True)
    updated_at = an = fields.DateTime(dump_only=True, allow_none=True)

    class Meta:
        # Define the order of fields in the output
        ordered = True

class CustomerUpdateSchema(Schema):
    """Schema for validating customer updates (all fields optional)."""
    name = fields.Str()
    email = fields.Email()
    phone = fields.Str()
    address = fields.Str()
    gst_number = fields.Str()

class CustomerListSchema(Schema):
    """Schema for the list of customers with aggregated data."""
    items = fields.List(fields.Nested(lambda: CustomerDetailSchema()))
    total = fields.Int()

class CustomerDetailSchema(CustomerSchema):
    """Extends the base schema to include read-only aggregated data for detail views."""
    status = fields.Str(dump_only=True, attribute='payment_status')
    aggregates = fields.Dict(dump_only=True)

# Schema for bulk operations (e.g., deletion)
class BulkDeleteSchema(Schema):
    ids = fields.List(fields.Str(), required=True)

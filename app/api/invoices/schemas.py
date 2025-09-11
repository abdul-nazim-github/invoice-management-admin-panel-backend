from marshmallow import Schema, fields, validate


# ------------------------
# Schema for invoice items
# ------------------------
class InvoiceItemSchema(Schema):
    product_id = fields.UUID(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


# ------------------------
# Schema for creating an invoice
# ------------------------
class InvoiceCreateSchema(Schema):
    invoice_number = fields.Str(required=True)
    customer_id = fields.UUID(required=True)
    due_date = fields.Date(required=False, allow_none=True)
    status = fields.Str(
        validate=validate.OneOf(["pending", "paid", "partial"]),
        load_default="pending",
    )
    tax_percent = fields.Decimal(as_string=True, load_default="0")
    discount_amount = fields.Decimal(   # ✅ fixed name
        as_string=True, load_default="0"
    )
    items = fields.List(fields.Nested(InvoiceItemSchema), required=True)


# ------------------------
# Schema for updating an invoice
# ------------------------
class InvoiceUpdateSchema(Schema):
    invoice_number = fields.Str()
    customer_id = fields.UUID()
    due_date = fields.Date(required=False, allow_none=True)
    status = fields.Str(validate=validate.OneOf(["pending", "paid", "partial"]))
    tax_percent = fields.Decimal(as_string=True)
    discount_amount = fields.Decimal(as_string=True)   # ✅ fixed name
    items = fields.List(fields.Nested(InvoiceItemSchema), required=False)


# ------------------------
# Schema for bulk delete invoices
# ------------------------
class InvoiceBulkDeleteSchema(Schema):
    ids = fields.List(
        fields.UUID(),
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "IDs are required"},
    )


# ------------------------
# Schema for filtering invoices (list API)
# ------------------------
class InvoiceFilterSchema(Schema):
    q = fields.Str(required=False, allow_none=True)  # search by invoice_number
    status = fields.Str(
        validate=validate.OneOf(["pending", "paid", "partial"]),
        required=False,
    )
    page = fields.Int(load_default=1)
    limit = fields.Int(load_default=10)
    # Cursor-based filters
    before = fields.DateTime(required=False, allow_none=True)  # fetch invoices before this datetime
    after = fields.DateTime(required=False, allow_none=True)   # fetch invoices after this datetime

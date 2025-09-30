from marshmallow import Schema, fields, validate
from app.schemas.payment_schema import PaymentSchema

class InvoiceItemSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))

class InvoiceSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    due_date = fields.Date(allow_none=True)
    items = fields.List(fields.Nested(InvoiceItemSchema), required=True, validate=validate.Length(min=1))
    status = fields.Str(validate=validate.OneOf(["Pending", "Paid", "Cancelled"]), default="Pending")
    discount_amount = fields.Decimal(places=2, as_string=True, allow_none=True)
    tax_percent = fields.Decimal(places=2, as_string=True, allow_none=True)
    initial_payment = fields.Nested(PaymentSchema, allow_none=True)

# Create an instance of the schema to be used in the application
invoice_schema = InvoiceSchema()

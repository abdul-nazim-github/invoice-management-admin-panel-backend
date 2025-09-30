from marshmallow import Schema, fields, validate, ValidationError
from decimal import ROUND_HALF_UP

class InvoiceItemSchema(Schema):
    """
    Schema for items within an invoice.
    """
    product_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Product ID must be a positive integer.")
    )
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Quantity must be at least 1.")
    )

class InitialPaymentSchema(Schema):
    """
    Schema for an initial payment made during invoice creation. This is load-only.
    """
    amount = fields.Decimal(
        places=2,
        rounding=ROUND_HALF_UP,
        required=True,
        validate=validate.Range(min=0.01, error="Initial payment amount must be positive.")
    )
    method = fields.Str(
        validate=validate.OneOf(['cash', 'card', 'upi', 'bank_transfer'], error="Invalid payment method."),
        load_default='cash'
    )
    reference_no = fields.Str(allow_none=True)

class InvoiceSchema(Schema):
    """
    Marshmallow schema for validating and serializing invoice data.
    """
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Customer ID must be a positive integer.")
    )
    due_date = fields.Date(
        required=True,
        format='%Y-%m-%d',
        error_messages={"required": "Due date is required.", "invalid": "Invalid date format. Use YYYY-MM-DD."}
    )
    subtotal_amount = fields.Decimal(as_string=True, dump_only=True)
    
    discount_amount = fields.Decimal(
        places=2, 
        rounding=ROUND_HALF_UP, 
        validate=validate.Range(min=0, error="Discount amount must be a non-negative number.")
    )
    tax_percent = fields.Decimal(
        places=2, 
        rounding=ROUND_HALF_UP, 
        validate=validate.Range(min=0, error="Tax percent must be a non-negative number.")
    )
    
    tax_amount = fields.Decimal(as_string=True, dump_only=True)
    total_amount = fields.Decimal(as_string=True, dump_only=True)
    amount_paid = fields.Decimal(as_string=True, dump_only=True)
    
    status = fields.Str(
        validate=validate.OneOf(['Pending', 'Paid', 'Overdue'], error="Invalid status. Must be one of: Pending, Paid, Overdue.")
    )
    items = fields.List(
        fields.Nested(InvoiceItemSchema),
        required=True,
        validate=validate.Length(min=1, error="Invoice must have at least one item.")
    )
    
    # For receiving an initial payment during creation
    initial_payment = fields.Nested(InitialPaymentSchema, required=False, load_only=True)
    
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

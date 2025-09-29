from marshmallow import Schema, fields, validate

class PaymentSchema(Schema):
    """
    Marshmallow schema for validating payment data. 
    """
    id = fields.Int(dump_only=True)
    invoice_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Invoice ID must be a positive integer.")
    )
    amount = fields.Decimal(
        as_string=False,
        required=True,
        validate=validate.Range(min=0.01, error="Payment amount must be positive.")
    )
    payment_date = fields.Date(
        required=True,
        format='%Y-%m-%d',
        error_messages={"required": "Payment date is required.", "invalid": "Invalid date format. Use YYYY-MM-DD."}
    )
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf(["cash", "credit_card", "bank_transfer", "paypal"], error="Invalid payment method.")
    )
    created_at = fields.DateTime(dump_only=True)

from marshmallow import Schema, fields, validate

class PaymentCreateSchema(Schema):
    amount = fields.Decimal(
        required=True,
        as_string=True,
        error_messages={"required": "Amount is required"}
    )
    payment_date = fields.Date(
        required=False,
        allow_none=True,
        load_default=None
    )
    method = fields.Str(
        required=False,
        load_default="upi",
        validate=validate.OneOf(["upi", "card", "cash", "netbanking", "wallet"]),
    )
    reference_no = fields.Str(required=False, allow_none=True)

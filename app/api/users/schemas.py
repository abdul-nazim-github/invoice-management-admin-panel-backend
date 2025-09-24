# app/api/users/schemas.py
from marshmallow import Schema, fields, validate

class UserProfileSchema(Schema):
    full_name = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    email = fields.Email(required=False, allow_none=True, validate=validate.Length(max=100))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))

class UserPasswordSchema(Schema):
    old_password = fields.Str(required=True, validate=validate.Length(min=6))
    new_password = fields.Str(required=True, validate=validate.Length(min=6))

class UserBillingSchema(Schema):
    billing_address = fields.Str(required=False, allow_none=True)
    billing_city = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    billing_state = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    billing_pin = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))
    billing_gst = fields.Str(required=False, allow_none=True, validate=validate.Length(max=50))

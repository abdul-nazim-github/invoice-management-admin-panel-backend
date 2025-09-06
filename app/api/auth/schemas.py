from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    username = fields.Str(
        required=True, 
        error_messages={"required": "Username is required"}
    )
    email = fields.Email(
        required=True, 
        error_messages={"required": "Email is required", "invalid": "Invalid email address"}
    )
    password = fields.Str(
        required=True, 
        validate=validate.Length(min=6, error="Password must be at least 6 characters"),
        error_messages={"required": "Password is required"}
    )
    name = fields.Str(required=False)

class LoginSchema(Schema):
    email = fields.Email(
        required=True, 
        error_messages={"required": "Email is required", "invalid": "Invalid email address"}
    )
    password = fields.Str(
        required=True,
        error_messages={"required": "Password is required"}
    )
    otp = fields.Str(required=False)

class Enable2FASchema(Schema):
    confirm = fields.Boolean(required=False)

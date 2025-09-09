from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    username = fields.Str(
        required=True, error_messages={"required": "Username is required"}
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Invalid email address",
        },
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, error="Password must be at least 8 characters"),
            validate.Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
                error="Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character",
            ),
        ],
        error_messages={"required": "Password is required"},
    )
    full_name = fields.Str(required=False)  # ✅ fixed field


class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Invalid email address",
        },
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, error="Password must be at least 8 characters"),
            validate.Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
                error="Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character",
            ),
        ],
        error_messages={"required": "Password is required"},
    )
    otp = fields.Str(required=False)


class Enable2FASchema(Schema):
    confirm = fields.Boolean(required=False)

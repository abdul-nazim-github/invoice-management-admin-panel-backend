from marshmallow import Schema, ValidationError, fields, validate

def validate_identifier(value):
    # allow email OR username
    if "@" in value:
        # basic email validation
        if not validate.Email(error="Invalid email address")(value):
            raise ValidationError("Invalid email address")
    else:
        # username rules (alphanumeric, _, -, 3-30 chars)
        if not validate.Regexp(
            r"^[a-zA-Z0-9._-]{3,30}$",
            error="Invalid username (3-30 chars, letters, numbers, . _ - allowed)"
        )(value):
            raise ValidationError("Invalid username")


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
    identifier = fields.Str(
        required=True,
        validate=validate_identifier,
        error_messages={"required": "Email or Username is required"},
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
    otp = fields.Str(required=False, allow_none=True)

class Enable2FASchema(Schema):
    confirm = fields.Boolean(required=False)

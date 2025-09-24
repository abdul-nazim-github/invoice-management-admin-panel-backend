# app/api/users/routes.py
import logging
import re
from typing import Any, Dict
from flask import Blueprint, request
from passlib.hash import bcrypt
from marshmallow import ValidationError
from pymysql import IntegrityError
import pyotp
from app.api.auth.schemas import LoginSchema, RegisterSchema
from app.utils.auth import require_auth, require_admin
from app.database.models.user_model import (
    create_user,
    update_user_2fa,
    update_user_profile,
    update_user_password,
    update_user_billing,
    find_user_by_id
)
from app.api.users.schemas import UserProfileSchema, UserPasswordSchema, UserBillingSchema
from app.utils.response import error_response, success_response

users_bp = Blueprint("users", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()
profile_schema = UserProfileSchema()
password_schema = UserPasswordSchema()


@users_bp.post("/register")
@require_auth
@require_admin
def register():
    try:
        data = request.json or {}
        validated: Dict[str, str] = register_schema.load(data)

        password_hash = bcrypt.hash(validated["password"])
        uid = create_user(
            validated["username"],
            validated["email"],
            password_hash,
            full_name=validated["full_name"],
        )

        return success_response(
            result={"id": uid}, message="User registered successfully", status=201
        )
    except ValidationError as ve:
        return error_response(
            message="Validation error",
            details=ve.messages,
            status=400,
        )

    except IntegrityError as ie:
        msg = str(ie)
        details = {}

        if "Duplicate entry" in msg:
            match = re.search(r"Duplicate entry '(.+)' for key '.*\.(.+)'", msg)
            if match:
                value, field = match.groups()
                details[field] = [f"Duplicate entry '{value}'"]
            else:
                details["error"] = [msg]

            return error_response(
                message="Duplicate entry", details=details, status=409
            )
        return error_response(
            message="Integrity error", details={"error": [msg]}, status=400
        )

    except Exception as e:
        print(e)
        return error_response(
            message="Something went wrong!", details={"error": [str(e)]}, status=500
        )


@users_bp.get("/me")
@require_auth
def me():
    user = find_user_by_id(request.user["sub"]) or {}
    return success_response(
            message="User details successfully",
            result=user,
        )


@users_bp.put("/profile")
@require_auth
def update_profile():
    data = request.json or {}
    try:
        validated: Dict[str, str] = profile_schema.load(data)
        updated_user = update_user_profile(
            request.user["sub"],
            **validated,
        )
        print('updated_user: ', updated_user)
        return success_response(
            message="Profile updated successfully",
            result=updated_user,
        )

    except ValidationError as e:
        # Handle schema validation errors
        print('e.messages: ', e.messages)
        return error_response(
            message="Validation Error",
            details=e.messages,
            status=400,
        )

    except KeyError as e:
        # Handle missing keys
        logging.exception("Missing required key in the request")
        return error_response(
            message=f"Missing required field: {str(e)}",
            status=400,
        )

    except Exception as e:
        # Catch all other unexpected errors
        logging.exception("Unexpected error while updating profile")
        return error_response(
            message="An unexpected error occurred while updating profile",
            details=str(e),
            status=500,
        )

@users_bp.put("/password")
@require_auth
def change_password():
    data = request.json or {}
    try:
        validated: Dict[str, str] = password_schema.load(data)
    except ValidationError as e:
        return error_response(
            message="Validation Error",
            details=e.messages,
            status=400,
        )

    user: Dict[str, Any] = find_user_by_id(request.user["sub"])
    if not bcrypt.verify(validated["old_password"], user["password_hash"]):
        return error_response(
            message="Validation Error",
            details="Old password is incorrect",
            status=400,
        )

    new_hash = bcrypt.hash(validated["new_password"])
    update_user_password(request.user["sub"], new_hash)
    return success_response(
            message="Password changed successfully",
            result={"Success": True},
        )


@users_bp.put("/billing")
@require_auth
def update_billing():
    data = request.json or {}
    schema = UserBillingSchema()
    try:
        validated: Dict[str, str] = schema.load(data)
    except ValidationError as e:
        return error_response(
            message="Validation Error",
            details=e.messages,
            status=400,
        )

    updated_user = update_user_billing(
        request.user["sub"],
        address=validated["billing_address"],
        city=validated["billing_city"],
        state=validated["billing_state"],
        pin=validated["billing_pin"],
        gst=validated["billing_gst"],
    )
    return success_response(
            message="Billing details updated successfully",
            result={"user": updated_user},
        )

@users_bp.post("/enable-2fa")
@require_auth
def enable_2fa():
    try:
        secret = pyotp.random_base32()
        updated_user = update_user_2fa(request.user["sub"], secret)
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=str(request.user["email"]), issuer_name="CodeOrbit Billing"
        )
        return success_response(
            message="2FA enabled successfully",
            result={"secret": secret, "otpauth_uri": uri, "user_info": updated_user},
        )
    except Exception as e:
        return error_response(message="Failed to enable 2FA", details=str(e))

# app/api/users/routes.py
from typing import Any, Dict
from flask import Blueprint, request
from passlib.hash import bcrypt
from marshmallow import ValidationError
import pyotp
from app.utils.auth import require_auth
from app.database.models.user_model import (
    update_user_2fa,
    update_user_profile,
    update_user_password,
    update_user_billing,
    find_user_by_id
)
from app.api.users.schemas import UserProfileSchema, UserPasswordSchema, UserBillingSchema
from app.utils.response import error_response, success_response

users_bp = Blueprint("users", __name__)


@users_bp.get("/me")
@require_auth
def me():
    user = find_user_by_id(request.user["sub"]) or {}
    public = {
        k: user.get(k)
        for k in ["id", "email", "username", "full_name", "role",
                  "billing_address", "billing_city", "billing_state", "billing_pin", "billing_gst"]
    }
    return success_response(
            message="User details successfully",
            result={"user": public},
        )


@users_bp.put("/profile")
@require_auth
def update_profile():
    data = request.json or {}
    schema = UserProfileSchema()
    try:
        validated: Dict[str, str] = schema.load(data)
    except ValidationError as e:
        return error_response(
            message="Validation Error",
            details=e.messages,
            status=400,
        )

    updated_user = update_user_profile(
        request.user["sub"],
        full_name=validated["full_name"],
        email=validated["email"]
    )
    return success_response(
            message="Profile updated successfully",
            result={"user": updated_user},
        )


@users_bp.put("/password")
@require_auth
def change_password():
    data = request.json or {}
    schema = UserPasswordSchema()
    try:
        validated: Dict[str, str] = schema.load(data)
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
        address=validated["bill_address"],
        city=validated["bill_city"],
        state=validated["bill_state"],
        pin=validated["bill_pin"],
        gst=validated["bill_gst"],
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

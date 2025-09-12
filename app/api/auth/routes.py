from typing import Dict
from flask import Blueprint, request, make_response, current_app
from passlib.hash import bcrypt
import pyotp
from marshmallow import ValidationError
from app.api.auth.schemas import LoginSchema
from app.database.models.user_model import find_user_by_email
from app.utils.auth import create_token, require_auth
from app.database.models.auth_model import blacklist_token, remove_expired_tokens
from app.utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)

login_schema = LoginSchema()

@auth_bp.post("/login")
def login():
    try:
        data = request.json or {}
        validated: Dict[str, str] = login_schema.load(data)
        email: str = validated.get("email")
        password: str = validated.get("password")
        otp: str = validated.get("otp")

        if not email or not password:
            return error_response("Email and password required", status=400)

        user = find_user_by_email(email)
        if not user or not bcrypt.verify(password, user["password_hash"]):
            return error_response("Invalid email or password", status=401)

        if user.get("twofa_secret"):
            if not otp:
                return error_response("OTP required", status=401)
            totp = pyotp.TOTP(user["twofa_secret"])
            if not totp.verify(str(otp)):
                return error_response("Invalid OTP", status=401)

        # Clean expired tokens
        remove_expired_tokens()

        token = create_token({"sub": user["id"], "email": user["email"], "role": user["role"]})
        if isinstance(token, tuple):
            return token

        resp = make_response(success_response(
            message="Login successful",
            result={"access_token": token, "user_info": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"]
            }}
        ))

        # Optionally store in cookie
        resp.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=current_app.config["JWT_EXPIRES_MIN"] * 60
        )
        return resp
    except ValidationError as ve:
        return error_response("Validation error", details=ve.messages, status=400)
    except Exception as e:
        return error_response("Login failed", details={"error": [str(e)]}, status=500)


@auth_bp.post("/logout")
@require_auth
def logout():
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("Unauthorized", status=401)

        token = auth_header.split(" ", 1)[1]
        blacklist_token(request.user["sub"], token)

        return success_response(message="Logged out successfully")
    except Exception as e:
        return error_response("Logout failed", details=str(e), status=500)

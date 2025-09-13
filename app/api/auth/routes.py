from typing import Dict
from flask import Blueprint, request
from passlib.hash import bcrypt
import pyotp
from marshmallow import ValidationError
from app.api.auth.schemas import LoginSchema
from app.database.models.user_model import find_user
from app.utils.auth import create_token, require_auth
from app.database.models.auth_model import blacklist_token, remove_expired_tokens
from app.utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)

login_schema = LoginSchema()

@auth_bp.post("/sign-in")
def sign_in():
    try:
        data = request.json or {}
        validated: Dict[str, str] = login_schema.load(data)
        user = find_user(validated["identifier"])

        if not user or not bcrypt.verify(validated["password"], user["password_hash"]):
            return error_response(
                "Invalid credentials",
                "Your email/username or password is incorrect.",
                401
            )

        if user.get("twofa_secret"):
            otp = validated.get("otp")
            if not otp or not pyotp.TOTP(user["twofa_secret"]).verify(str(otp)):
                return error_response("Invalid OTP", "Please enter a valid OTP.", 401)

        remove_expired_tokens()
        token = create_token({"sub": user["id"], "email": user["email"], "role": user["role"]})

        return success_response(
                message="Sign-in successful",
                result={
                    "access_token": token,
                    "user_info": {
                        "id": user["id"],
                        "email": user["email"],
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "role": user["role"]
                    }
                }
            )

    except ValidationError as ve:
        return error_response("Validation error", ve.messages, 400)
    except Exception as e:
        return error_response("Sign-in failed", str(e), 500)


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

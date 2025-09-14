import re
from typing import Dict
from flask import Blueprint, request
from passlib.hash import bcrypt
from pymysql import IntegrityError
import pyotp
from marshmallow import ValidationError
from app.api.auth.schemas import LoginSchema, RegisterSchema
from app.database.models.user_model import create_user, find_user
from app.utils.auth import create_token, require_auth
from app.database.models.auth_model import blacklist_token, remove_expired_tokens
from app.utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.post("/register")
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

@auth_bp.post("/sign-in")
def sign_in():
    try:
        data = request.json or {}
        validated: Dict[str, str] = login_schema.load(data)
        user = find_user(validated["identifier"])

        if not user or not bcrypt.verify(validated["password"], user["password_hash"]):
            return error_response(
                type="invalid_credentials",
                message="Invalid credentials",
                details="Your email/username or password is incorrect.",
                status=401
            )

        if user.get("twofa_secret"):
            otp = validated.get("otp")
            if not otp or not pyotp.TOTP(user["twofa_secret"]).verify(str(otp)):
                return error_response(
                    type="invalid_otp",
                    message="Invalid OTP",
                    details="Please enter a valid OTP.",
                    status=401
                )

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
        return error_response(
            type="validation_error",
            message="Invalid Credentials",
            details=ve.messages,
            status=400
        )
    except Exception as e:
        return error_response(
            type="server_error",
            message="Sign-in failed",
            details=str(e),
            status=500
        )


@auth_bp.post("/sign-out")
@require_auth
def sign_out():
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("Unauthorized", status=401)

        token = auth_header.split(" ", 1)[1]
        blacklist_token(request.user["sub"], token)

        return success_response(message="Logged out successfully")
    except Exception as e:
        return error_response("Sign-out failed", details=str(e), status=500)

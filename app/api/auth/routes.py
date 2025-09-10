# =============================
# app/api/auth/routes.py
# =============================
import re
from flask import Blueprint, request
from passlib.hash import bcrypt
import pyotp
from typing import Dict
from pymysql.err import IntegrityError
from marshmallow import ValidationError
from app.api.auth.schemas import Enable2FASchema, LoginSchema, RegisterSchema
from app.utils.auth import create_token
from app.utils.response import success_response, error_response
from app.database.models.user_model import (
    find_user_by_email,
    create_user,
)

auth_bp = Blueprint("auth", __name__)

# Schemas
register_schema = RegisterSchema()
login_schema = LoginSchema()
enable_2fa_schema = Enable2FASchema()


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


@auth_bp.post("/login")
def login():
    try:
        data = request.json or {}
        validated: Dict[str, str] = login_schema.load(data)
        password: str = validated.get("password")
        otp: str = validated.get("otp")

        user = find_user_by_email(validated["email"])
        if not user:
            return error_response(
                message="Invalid credentials",
                details={"email": ["User not exist"]},
                status=401,
            )

        if not bcrypt.verify(password, user["password_hash"]):
            return error_response(
                message="Invalid credentials",
                details={"password": ["Invalid password"]},
                status=401,
            )

        if user.get("twofa_secret"):
            if not otp:
                return error_response(
                    message="OTP required",
                    details={"otp": ["OTP is required"]},
                    status=401,
                )
            totp = pyotp.TOTP(user["twofa_secret"])
            if not totp.verify(str(otp)):
                return error_response(
                    message="Invalid OTP", details={"otp": ["Invalid OTP"]}, status=401
                )

        token = create_token(
            {"sub": user["id"], "email": user["email"], "role": user["role"]}
        )

        if isinstance(token, tuple):
            return token

        user_info = {
            k: user[k]
            for k in ["id", "email", "username", "full_name", "role"]  # ✅ fixed field
        }

        return success_response(
            result={"access_token": token, "user_info": user_info},
            message="Sign-in successful",
        )

    except ValidationError as ve:
        return error_response(
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except Exception as e:
        return error_response(
            message="Sign-in failed", details={"error": [str(e)]}, status=500
        )

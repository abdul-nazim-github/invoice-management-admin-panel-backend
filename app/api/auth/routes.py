# =============================
# app/api/auth/routes.py
# =============================
from flask import Blueprint, request
from passlib.hash import bcrypt
import pyotp
from pymysql.err import IntegrityError
from app.utils.auth import create_token, require_auth
from app.utils.response import success_response, error_response
from app.database.models.user_model import (
    find_user_by_email,
    find_user_by_id,
    update_user_password,
    update_user_2fa,
    create_user,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    try:
        data = request.json
        username = data["username"]
        email = data["email"]
        password = data["password"]
        name = data.get("name")

        password_hash = bcrypt.hash(password)
        uid = create_user(username, email, password_hash, name=name)

        return success_response(result={"user_id": uid}, message="User registered successfully", status=201)
    except IntegrityError as e:
        # Duplicate entry handling
        if "Duplicate entry" in str(e):
            return error_response(message="Username or email already exists", details=str(e), status=409)
        return error_response(message="Database integrity error", details=str(e))

    except Exception as e:
        return error_response(message="Registration failed", details=str(e))


@auth_bp.post("/login")
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        otp = data.get("otp")

        user = find_user_by_email(email)
        if not user:
            return error_response(message="Invalid credentials", details="User not found", status=401)

        if not bcrypt.verify(password, user["password_hash"]):
            return error_response(message="Invalid credentials", details="Wrong password", status=401)

        # Handle 2FA
        if user.get("twofa_secret"):
            if not otp:
                return error_response(message="OTP required", status=401)
            totp = pyotp.TOTP(user["twofa_secret"])
            if not totp.verify(str(otp)):
                return error_response(message="Invalid OTP", status=401)

        token = create_token({"sub": user["id"], "email": user["email"], "role": user["role"]})

        # If create_token failed and returned an error_response (tuple)
        if isinstance(token, tuple):  
            return token  

        user_info = {k: user[k] for k in ["id", "email", "username", "name", "role"]}
        return success_response(
            result={"access_token": token, "user": user_info},
            message="Sign-in successful"
        )
    except Exception as e:
        return error_response(message="Sign-in failed", details=str(e))

@auth_bp.post("/enable-2fa")
@require_auth
def enable_2fa():
    try:
        secret = pyotp.random_base32()
        update_user_2fa(request.user["sub"], secret)
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=str(request.user["email"]), issuer_name="CodeOrbit Billing"
        )
        return success_response(result={"secret": secret, "otpauth_uri": uri}, message="2FA enabled successfully")
    except Exception as e:
        return error_response(message="Failed to enable 2FA", details=str(e))

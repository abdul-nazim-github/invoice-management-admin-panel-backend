# =============================
# app/utils/auth.py (JWT + decorators)
# =============================
import time
import jwt
from flask import current_app, request, jsonify
from functools import wraps

from app.utils.response import error_response


def create_token(payload: dict):
    try:
        exp = int(time.time()) + current_app.config["JWT_EXPIRES_MIN"] * 60
        payload = {
            **payload,
            "exp": exp,
            "iat": int(time.time()),  # issued at
        }

        token = jwt.encode(
            payload,
            current_app.config["JWT_SECRET"],
            algorithm="HS256"
        )

        # Normalize to str (PyJWT v1 may return bytes)
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        return token
    except Exception as e:
        # Instead of crashing, return a proper error response
        return error_response(message="Failed to create token", details=str(e), status=500)

def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return error_response(message="Authentication failed", details="Token has expired", status=401)
    except jwt.InvalidTokenError:
        return error_response(message="Authentication failed", details="Invalid token", status=401)
    except Exception as e:
        return error_response(message="Authentication failed", details=str(e), status=401)

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        try:
            data = decode_token(token)
            request.user = data  # attach to request
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
        return fn(*args, **kwargs)

    return wrapper
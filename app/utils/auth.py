# =============================
# app/utils/auth.py
# JWT utilities + authentication decorators
# =============================
import time
import jwt
from flask import current_app, request
from functools import wraps

from app.utils.response import error_response


def create_token(payload: dict[str, object]):
    """
    Create a signed JWT access token.

    Args:
        payload (dict): The claims to include in the token.
                        Typically includes user id, email, role, etc.

    Returns:
        str | (Response, int): 
            - On success: Encoded JWT as a string.
            - On failure: Flask error_response (JSON + HTTP status).

    Notes:
        - Adds "exp" (expiration) and "iat" (issued at) claims automatically.
        - Expiration is based on current_app.config["JWT_EXPIRES_MIN"] (in minutes).
        - Uses HS256 algorithm with current_app.config["JWT_SECRET"].
    """
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
        return error_response(
            message="Failed to create token",
            details=str(e),
            status=500
        )


def decode_token(token: str):
    """
    Decode and verify a JWT token.

    Args:
        token (str): The JWT access token as a string.

    Returns:
        dict | (Response, int):
            - On success: Decoded token payload (dict).
            - On failure: Flask error_response (JSON + HTTP status).

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token signature is invalid or corrupted.
    """
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return error_response(
            message="Authentication failed",
            details="Token has expired",
            status=401
        )
    except jwt.InvalidTokenError:
        return error_response(
            message="Authentication failed",
            details="Invalid token",
            status=401
        )
    except Exception as e:
        return error_response(
            message="Authentication failed",
            details=str(e),
            status=401
        )


def require_auth(fn):
    """
    Decorator to protect Flask routes with JWT authentication.

    Usage:
        @app.route("/protected")
        @require_auth
        def protected():
            return jsonify({"message": "You are authenticated!"})

    Behavior:
        - Expects `Authorization: Bearer <token>` header.
        - Decodes token and attaches decoded payload to `request.user`.
        - If invalid/missing token, returns 401 Unauthorized response.

    Args:
        fn (callable): The route function to wrap.

    Returns:
        callable: The wrapped route function.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error_response(
                message="Unauthorized",
                details="Missing or invalid Authorization header",
                status=401
            )

        token = auth.split(" ", 1)[1]
        data = decode_token(token)

        # If decode_token already returned an error_response → just return it
        if isinstance(data, tuple):
            return data

        # Attach decoded token payload to request object
        request.user = data  
        return fn(*args, **kwargs)

    return wrapper

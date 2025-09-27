# =============================
# app/utils/auth.py
# JWT utilities + authentication decorators
# =============================
import time
import jwt
from flask import current_app, request
from functools import wraps

from app.database.models.auth_model import is_token_blacklisted
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
        - Uses HS256 algorithm with current_app.config["JWT_SECRET_KEY"].
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
            current_app.config["JWT_SECRET_KEY"],
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
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return error_response(
            message="Authentication failed",
            details="Token has expired. Please log in again.",
            status=401
        )
    except jwt.InvalidTokenError:
        return error_response(
            message="Authentication failed",
            details="Invalid token. Please log in again.",
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
    Authentication decorator to protect endpoints.

    Verifies the presence and validity of a JWT 'Bearer' token in the
    Authorization header. Attaches the decoded token payload to `request.user`.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return error_response(
                message="Authentication Required",
                details="Authorization header is missing. Please provide a 'Bearer' token.",
                status=401
            )

        if not auth_header.startswith("Bearer "):
            return error_response(
                message="Invalid Authorization Scheme",
                details="Authorization header must use the 'Bearer' scheme.",
                status=401
            )

        token = auth_header.split(" ", 1)[1]

        # Check if token has been blacklisted (e.g., after logout)
        if is_token_blacklisted(token):
            return error_response(
                message="Unauthorized",
                details="Token has been revoked. Please log in again.",
                status=401
            )

        # Decode the token and handle any errors
        decoded_payload = decode_token(token)
        if isinstance(decoded_payload, tuple):  # Indicates an error response was returned
            return decoded_payload

        # Attach user data to the request object for use in the endpoint
        request.user = decoded_payload
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    """
    Authorization decorator to ensure a user has one of the specified roles.

    This decorator must be placed AFTER the @require_auth decorator on an endpoint.

    Args:
        *roles (str): A list of role names that are allowed to access the endpoint.

    Returns:
        A decorator function that checks the user's role.

    Example:
        @bp.route('/admin/dashboard')
        @require_auth
        @require_role('admin', 'manager')
        def admin_dashboard():
            return success_response(data={"message": "Welcome Admin or Manager!"})
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not hasattr(request, 'user'):
                # This should not happen if @require_auth is used first
                return error_response(
                    message="Authentication Error",
                    details="User information not found. Ensure @require_auth is used before @require_role.",
                    status=500
                )

            user_role = request.user.get('role')
            if user_role not in roles:
                return error_response(
                    message="Forbidden",
                    details=f"You do not have the necessary permissions to access this resource. Required roles: {', '.join(roles)}.",
                    status=403
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Convenience decorator for the common case of requiring an 'admin' role
require_admin = require_role('admin')

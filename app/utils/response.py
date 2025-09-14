from flask import jsonify

from flask import jsonify


def success_response(result=None, message="Success", meta=None, status=200):
    """
    Standard success response
    - result: actual payload (dict, list, etc.)
    - message: user-friendly message
    - meta: extra info (pagination, filters, etc.)
    - status: HTTP status code
    """
    # Always wrap results in "results" inside "data"
    return (
        jsonify(
            {
                "success": True,
                "message": message,
                "data": {
                    "results": result if result is not None else [],
                    "meta": meta if meta else {},
                },
            }
        ),
        status,
    )


def error_response(type="server_error", message="Error", details=None, status=400):
    return (
        jsonify({
            "success": False,
            "type": type,         # e.g., validation_error, invalid_credentials, invalid_otp, server_error
            "message": message,   # high-level error message for UI toast title
            "error": { "details": details },  # detailed info (for form errors, etc.)
        }),
        status,
    )

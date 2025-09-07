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


def error_response(message="Error", details=None, status=400):
    return (
        jsonify({"success": False, "message": message, "error": {"details": details}}),
        status,
    )

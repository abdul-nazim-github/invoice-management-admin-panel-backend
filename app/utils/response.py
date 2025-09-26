from flask import current_app, jsonify
import json

def success_response(result=None, message="Success", meta=None, status=200):
    """
    Creates a standardized success JSON response.
    """
    return (
        current_app.response_class(
            response=json.dumps(
                {
                    "success": True,
                    "message": message,
                    "data": {"results": result or [], "meta": meta or {}},
                },
            ),
            status=status,
            mimetype="application/json",
        ),
        status,
    )

def error_response(type="server_error", message=None, details=None, status=400):
    """
    Creates a standardized error JSON response with default messages.
    """
    # Centralized mapping of error types to user-friendly messages
    error_messages = {
        "validation_error": "Invalid input provided. Please check the details.",
        "not_found": "The requested resource could not be found.",
        "unauthorized": "Authentication credentials were not provided or were invalid.",
        "forbidden": "You do not have permission to perform this action.",
        "server_error": "An unexpected error occurred on our end. Please try again later.",
    }

    # Use the default message for the type if no specific message is provided
    response_message = message or error_messages.get(type, "An unknown error occurred.")

    return (
        jsonify({
            "success": False,
            "type": type,
            "message": response_message,
            "error": {"details": details if details else {}},
        }),
        status,
    )

def normalize_row(row):
    if row is None:
        return None
    return dict(row)

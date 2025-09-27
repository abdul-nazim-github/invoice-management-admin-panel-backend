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
    Creates a standardized, UI-friendly error JSON response.
    """
    # Centralized mapping of error types to user-friendly messages for fallback
    error_messages = {
        "validation_error": "Invalid input provided. Please check the details.",
        "not_found": "The requested resource could not be found.",
        "unauthorized": "Authentication credentials were not provided or were invalid.",
        "forbidden": "You do not have permission to perform this action.",
        "server_error": "An unexpected error occurred on our end. Please try again later.",
    }

    # Use the specific message if provided, otherwise fallback to the type-based message
    response_message = message or error_messages.get(type, "An unknown error occurred.")
    
    # For server errors in non-debug mode, do not send back detailed implementation errors.
    if type == "server_error" and not current_app.debug:
        response_message = "An unexpected error occurred on our end. Please try again later."
        details = None # Don't leak details

    response_data = {
        "success": False,
        "message": response_message,
    }
    
    # Only include details if they are present and not empty
    if details:
        response_data["details"] = details

    return (
        jsonify(response_data),
        status,
    )

def normalize_row(row):
    if row is None:
        return None
    return dict(row)

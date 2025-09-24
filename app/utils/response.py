from flask import current_app, jsonify
import json

def success_response(result=None, message="Success", meta=None, status=200):
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

def error_response(type="server_error", message="Error", details=None, status=400):
    return (
        jsonify({
            "success": False,
            "type": type,          # e.g., validation_error, invalid_credentials, server_error
            "message": message,    # high-level error message for UI
            "error": {"details": details if details else {}},
        }),
        status,
    )

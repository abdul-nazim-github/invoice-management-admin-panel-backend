
from flask import current_app
import json
from decimal import Decimal
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle special data types like Decimal and datetime.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # If the number is a whole number, return it as an integer.
            if obj == obj.to_integral_value():
                return int(obj)
            # Otherwise, convert to a formatted string to preserve trailing zeros.
            # This is the industry-standard and ONLY way to guarantee precision.
            else:
                return "{:.2f}".format(obj)

        if isinstance(obj, datetime):
            # Convert datetime to ISO 8601 string format.
            return obj.isoformat()
        return super().default(obj)

def success_response(result=None, message="Success", meta=None, status=200):
    """
    Creates a standardized success JSON response using the custom encoder.
    """
    return (
        current_app.response_class(
            response=json.dumps(
                {
                    "success": True,
                    "message": message,
                    "data": {"results": result or [], "meta": meta or {}},
                },
                cls=CustomJSONEncoder  # Use the custom encoder
            ),
            status=status,
            mimetype="application/json",
        ),
        status,
    )

def error_response(error_code="bad_request", message="An error occurred.", details=None, status=400):
    """
    Creates a standardized error JSON response.
    """
    return (
        current_app.response_class(
            response=json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": message,
                        "details": details or {},
                    },
                }
            ),
            status=status,
            mimetype="application/json",
        ),
        status,
    )

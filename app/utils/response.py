
from flask import current_app
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle special data types like Decimal and datetime.
    It implements specific rounding and formatting rules for Decimals.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # First, round the Decimal to 2 decimal places, which handles the 24.999 -> 25 case.
            rounded_obj = obj.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # If the rounded number is a whole number, return it as an integer.
            if rounded_obj == rounded_obj.to_integral_value():
                return int(rounded_obj)
            # Otherwise, convert to a string to preserve the exact decimal places (e.g., "24.30").
            else:
                return "{:.2f}".format(rounded_obj)

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

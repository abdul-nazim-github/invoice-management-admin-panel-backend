from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union
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

def normalize_value(value: Any) -> Any:
    """Normalize a single DB value (e.g., Decimal → float)."""
    if isinstance(value, Decimal):
        return float(value)
    return value

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}

def normalize_rows(rows: Union[List[Dict[str, Any]], Tuple[Dict[str, Any], ...]]) -> List[Dict[str, Any]]:
    return [normalize_row(r) for r in rows]
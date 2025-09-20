from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union
from flask import jsonify

def success_response(result=None, message="Success", meta=None, status=200):
    """
    Standard success response
    - result: actual payload (dict, list, etc.)
    - message: user-friendly message
    - meta: extra info (pagination, filters, etc.)
    - status: HTTP status code
    """
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
            "type": type,          # e.g., validation_error, invalid_credentials, server_error
            "message": message,    # high-level error message for UI
            "error": {"details": details if details else {}},
        }),
        status,
    )


def normalize_value(value: Any) -> Any:
    """
    Normalize a single DB value for JSON response:
    - Decimal → string (preserves precision)
    - datetime → ISO string
    - other types → unchanged
    """
    if isinstance(value, Decimal):
        return str(value)  # keep precision
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize all values in a DB row."""
    if not row:
        return {}
    return {k: normalize_value(v) for k, v in row.items()}


def normalize_rows(rows: Union[List[Dict[str, Any]], Tuple[Dict[str, Any], ...]]) -> List[Dict[str, Any]]:
    """Normalize multiple DB rows."""
    return [normalize_row(r) for r in rows]

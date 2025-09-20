from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union
from flask import current_app, jsonify
import json

class DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            # Format with two decimal places
            return "{:.2f}".format(o)
        return super().default(o)
    
def success_response(result=None, message="Success", meta=None, status=200):
    return (
        current_app.response_class(
            response=json.dumps(
                {
                    "success": True,
                    "message": message,
                    "data": {"results": result or [], "meta": meta or {}},
                },
                cls=DecimalEncoder,
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

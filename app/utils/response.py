from flask import jsonify

def success_response(result=None, message="Success", status=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": {
            # always wrap inside "result"
            "result": result if result is not None else []
        }
    }), status

def error_response(message="Error", details=None, status=400):
    return jsonify({
        "success": False,
        "message": message,
        "error": {
            "details": details
        }
    }), status


# =============================
# app/api/customers/routes.py
# =============================
from flask import Blueprint, request, jsonify
from app.utils.auth import require_auth
from pymysql.err import IntegrityError
from app.utils.pagination import get_pagination
from app.database.models.customer_model import (
    create_customer, get_customer, list_customers, update_customer, bulk_delete_customers, customer_aggregates
)

customers_bp = Blueprint("customers", __name__)


@customers_bp.post("/")
@require_auth
def add_customer():
    data = request.json
    try:
        cid = create_customer(
            data["name"],
            data.get("email"),
            data.get("phone"),
            data.get("address"),
            data.get("gst_number"),
            data.get("status", "active"),
        )
        return jsonify({"message": "created", "id": cid}), 201

    except IntegrityError as e:
        # Duplicate email or constraint violation
        return jsonify({
            "error": "Conflict",
            "details": str(e)
        }), 409  

    except Exception as e:
        # Catch-all fallback
        return jsonify({
            "error": "Something went wrong",
            "details": str(e)
        }), 500
        
@customers_bp.get("/")
@require_auth
def list_():
    page, limit, offset = get_pagination()
    q = request.args.get("q")
    status = request.args.get("status")  # active/inactive
    rows, total = list_customers(q=q, status=status, offset=offset, limit=limit)
    return jsonify({"items": rows, "total": total, "page": page, "limit": limit})


@customers_bp.get("/<int:customer_id>")
@require_auth
def detail(customer_id):
    customer = get_customer(customer_id)
    if not customer:
        return jsonify({"error": "not found"}), 404
    agg = customer_aggregates(customer_id)
    return jsonify({"customer": customer, **agg})


@customers_bp.put("/<int:customer_id>")
@require_auth
def update(customer_id):
    data = request.json
    update_customer(customer_id, **data)
    return jsonify({"message": "updated"})


@customers_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    ids = request.json.get("ids", [])
    deleted = bulk_delete_customers(ids)
    return jsonify({"deleted": deleted})

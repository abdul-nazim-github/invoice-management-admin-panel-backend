# =============================
# app/api/products/routes.py
# =============================
from flask import Blueprint, request, jsonify
from app.utils.auth import require_auth
from app.utils.pagination import get_pagination
from app.database.models.product_model import (
    create_product, list_products, get_product, update_product, bulk_delete_products
)

products_bp = Blueprint("products", __name__)


@products_bp.post("/")
@require_auth
def add_product():
    data = request.json
    pid = create_product(data["product_code"], data["name"], data.get("description"), data["price"], data.get("stock", 0), data.get("status", "active"))
    return jsonify({"message": "created", "id": pid}), 201


@products_bp.get("/")
@require_auth
def list_():
    page, limit, offset = get_pagination()
    q = request.args.get("q")
    status = request.args.get("status")  # active/inactive
    rows, total = list_products(q=q, status=status, offset=offset, limit=limit)
    return jsonify({"items": rows, "total": total, "page": page, "limit": limit})


@products_bp.get("/<int:product_id>")
@require_auth
def detail(product_id):
    product = get_product(product_id)
    if not product:
        return jsonify({"error": "not found"}), 404
    return jsonify(product)


@products_bp.put("/<int:product_id>")
@require_auth
def update(product_id):
    data = request.json
    update_product(product_id, **data)
    return jsonify({"message": "updated"})


@products_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    ids = request.json.get("ids", [])
    deleted = bulk_delete_products(ids)
    return jsonify({"deleted": deleted})

# =============================
# app/api/invoices/routes.py
# =============================
from flask import Blueprint, request, jsonify
from datetime import date
from app.utils.auth import require_auth
from app.utils.pagination import get_pagination
from app.database.models.invoice_model import (
    create_invoice, get_invoice, list_invoices, update_invoice, bulk_delete_invoices
)
from app.database.models.invoice_item_model import add_invoice_item, get_items_by_invoice
from app.database.models.product_model import get_product
from app.database.models.payment_model import create_payment, sum_payments_for_invoice

invoices_bp = Blueprint("invoices", __name__)


@invoices_bp.post("/")
@require_auth
def create():
    data = request.json
    items = data.get("items", [])

    # Calculate total from product prices (snapshot price at time of sale)
    total = 0.0
    for it in items:
        prod = get_product(it["product_id"]) or {}
        total += float(prod.get("price", 0)) * int(it.get("quantity", 1))

    invoice_id = create_invoice(
        data["invoice_number"],
        data["customer_id"],
        request.user["sub"],
        data.get("invoice_date", str(date.today())),
        data.get("due_date"),
        total,
        data.get("status", "unpaid")
    )

    for it in items:
        prod = get_product(it["product_id"])
        add_invoice_item(invoice_id, it["product_id"], it["quantity"], prod["price"])

    return jsonify({"message": "created", "id": invoice_id, "total": total}), 201


@invoices_bp.get("/")
@require_auth
def list_():
    page, limit, offset = get_pagination()
    q = request.args.get("q")
    status = request.args.get("status")  # unpaid/paid/cancelled or None
    rows, total = list_invoices(q=q, status=status, offset=offset, limit=limit)

    # Attach paid/due quick fields
    enriched = []
    for inv in rows:
        paid = sum_payments_for_invoice(inv["id"])
        inv["paid_amount"] = paid
        inv["due_amount"] = float(inv["total_amount"]) - paid
        enriched.append(inv)

    return jsonify({"items": enriched, "total": total, "page": page, "limit": limit})


@invoices_bp.get("/<int:invoice_id>")
@require_auth
def detail(invoice_id):
    inv = get_invoice(invoice_id)
    if not inv:
        return jsonify({"error": "not found"}), 404
    items = get_items_by_invoice(invoice_id)
    paid = sum_payments_for_invoice(invoice_id)
    return jsonify({"invoice": inv, "items": items, "paid_amount": paid, "due_amount": float(inv["total_amount"]) - paid})


@invoices_bp.put("/<int:invoice_id>")
@require_auth
def update(invoice_id):
    data = request.json
    update_invoice(invoice_id, **data)
    return jsonify({"message": "updated"})


@invoices_bp.post("/<int:invoice_id>/pay")
@require_auth
def pay(invoice_id):
    data = request.json
    create_payment(invoice_id, data["amount"], data.get("payment_date", str(date.today())), data.get("method", "upi"), data.get("reference_no"))
    return jsonify({"message": "payment recorded"})


@invoices_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    ids = request.json.get("ids", [])
    deleted = bulk_delete_invoices(ids)
    return jsonify({"deleted": deleted})

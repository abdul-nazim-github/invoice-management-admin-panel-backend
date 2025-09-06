# =============================
# app/api/dashboard/routes.py (metrics)
# =============================
from flask import Blueprint, jsonify
from app.utils.auth import require_auth
from app.database.base import get_db_connection


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@require_auth
def metrics():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_amount),0) AS revenue FROM invoices WHERE status IN ('paid','unpaid')")
        revenue = float(cur.fetchone()["revenue"])  # all revenue billed
        cur.execute("SELECT COUNT(*) AS c FROM products WHERE status='active'")
        active_products = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM customers")
        customers = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM invoices WHERE status='unpaid'")
        pending_invoices = cur.fetchone()["c"]
    conn.close()
    return jsonify({
        "total_revenue": revenue,
        "active_products": active_products,
        "customers": customers,
        "pending_invoices": pending_invoices,
    })

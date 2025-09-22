# app/database/models/dashboard_model.py
from decimal import Decimal
from typing import Any, Dict
from app.database.base import get_db_connection

def get_dashboard_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Total revenue (only non-deleted invoices)
            cur.execute("""
                SELECT COALESCE(SUM(total_amount), 0) AS total_revenue 
                FROM invoices 
                WHERE status='Paid' AND deleted_at IS NULL
            """)
            row = cur.fetchone()
            total_revenue = Decimal(row["total_revenue"]) if row and row["total_revenue"] is not None else Decimal("0.00")

            # Total customers (non-deleted)
            cur.execute("SELECT COUNT(*) AS total_customers FROM customers WHERE deleted_at IS NULL")
            row = cur.fetchone()
            total_customers = row["total_customers"] if row else 0

            # Pending invoices (non-deleted)
            cur.execute("SELECT COUNT(*) AS pending_invoices FROM invoices WHERE status='Pending' AND deleted_at IS NULL")
            row = cur.fetchone()
            pending_invoices = row["pending_invoices"] if row else 0

            # Total products (non-deleted)
            cur.execute("SELECT COUNT(*) AS total_products FROM products WHERE deleted_at IS NULL")
            row = cur.fetchone()
            total_products = row["total_products"] if row else 0

            return {
                "total_revenue": total_revenue,
                "total_customers": total_customers,
                "pending_invoices": pending_invoices,
                "total_products": total_products,
            }
    finally:
        conn.close()

def get_sales_performance() -> list[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    DATE_FORMAT(created_at, '%%Y-%%m') AS month,
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM invoices
                WHERE status = 'Paid'
                GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
                ORDER BY month ASC
            """)
            rows = cur.fetchall()
            return [{"month": row["month"], "revenue": float(row["revenue"])} for row in rows]
    finally:
        conn.close()
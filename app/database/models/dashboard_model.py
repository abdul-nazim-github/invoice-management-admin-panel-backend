# app/database/models/dashboard_model.py
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict
from dateutil.relativedelta import relativedelta  # ✅ Missing import
from app.database.base import get_db_connection


def calculate_percentage_change(current: Decimal, previous: Decimal) -> Decimal:
    """
    Calculate the percentage change from previous to current.

    Returns:
        Positive Decimal if current > previous,
        Negative Decimal if current < previous,
        0.0 if both are 0.

    Special case:
        If previous is 0:
            - Returns 100.0 if current > 0 (full growth)
            - Returns 0.0 if current == 0
    """
    if previous == 0:
        return Decimal("100.0") if current > 0 else Decimal("0.0")
    return Decimal(((current - previous) / previous) * 100)


def get_dashboard_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            today = date.today()
            first_day_current_month = today.replace(day=1)
            first_day_last_month = first_day_current_month - relativedelta(months=1)
            last_day_last_month = first_day_current_month - timedelta(days=1)

            # Total revenue - current month
            cur.execute(
                """
                SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM invoices
                WHERE status='Paid' AND deleted_at IS NULL
                  AND created_at >= %s
            """,
                (first_day_current_month,),
            )
            row = cur.fetchone() or {}
            total_revenue = Decimal(row.get("total_revenue", 0))

            # Total revenue - last month
            cur.execute(
                """
                SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM invoices
                WHERE status='Paid' AND deleted_at IS NULL
                  AND created_at BETWEEN %s AND %s
            """,
                (first_day_last_month, last_day_last_month),
            )
            row = cur.fetchone() or {}
            last_month_revenue = Decimal(row.get("total_revenue", 0))

            revenue_change_percent = calculate_percentage_change(
                total_revenue, last_month_revenue
            )

            # Total customers - current month
            cur.execute(
                """
                SELECT COUNT(*) AS total_customers
                FROM customers
                WHERE deleted_at IS NULL
                  AND created_at >= %s
            """,
                (first_day_current_month,),
            )
            row = cur.fetchone() or {}
            total_customers = int(row.get("total_customers", 0))

            # Total customers - last month
            cur.execute(
                """
                SELECT COUNT(*) AS total_customers
                FROM customers
                WHERE deleted_at IS NULL
                  AND created_at BETWEEN %s AND %s
            """,
                (first_day_last_month, last_day_last_month),
            )
            row = cur.fetchone() or {}
            last_month_customers = int(row.get("total_customers", 0))

            customers_change_percent = calculate_percentage_change(
                Decimal(total_customers), Decimal(last_month_customers)
            )

            # Other counts
            cur.execute(
                "SELECT COUNT(*) AS total_invoices FROM invoices WHERE deleted_at IS NULL"
            )
            row = cur.fetchone() or {}
            total_invoices = int(row.get("total_invoices", 0))

            cur.execute(
                "SELECT COUNT(*) AS pending_invoices FROM invoices WHERE status='Pending' AND deleted_at IS NULL"
            )
            row = cur.fetchone() or {}
            pending_invoices = int(row.get("pending_invoices", 0))

            cur.execute(
                "SELECT COUNT(*) AS total_products FROM products WHERE deleted_at IS NULL"
            )
            row = cur.fetchone() or {}
            total_products = int(row.get("total_products", 0))

            return {
                "total_revenue": total_revenue,
                "revenue_change_percent": revenue_change_percent,  # Decimal
                "total_customers": total_customers,  # int
                "customers_change_percent": customers_change_percent,  # Decimal
                "total_invoices": total_invoices,  # int
                "pending_invoices": pending_invoices,  # int
                "total_products": total_products,  # int
            }
    finally:
        conn.close()

def get_sales_performance() -> list[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    DATE_FORMAT(created_at, '%%Y-%%m') AS month,
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM invoices
                WHERE status = 'Paid'
                GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
                ORDER BY month ASC
            """
            )
            rows = cur.fetchall()
            return [
                {"month": row["month"], "revenue": float(row["revenue"])}
                for row in rows
            ]
    finally:
        conn.close()

# app/database/models/dashboard_model.py
import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
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

def get_sales_performance() -> List[Dict[str, Any]]:
    """
    Returns last 6 months sales performance with:
    - month: 'Apr 2025'
    - revenue: total revenue for the month
    - invoice_count: number of invoices
    Only includes invoices where deleted_at IS NULL
    """
    conn = get_db_connection()
    try:
        # Get first day of current month
        today = date.today()
        months = []
        for i in range(5, -1, -1):  # Last 6 months
            month_date = date(today.year, today.month, 1)
            # Subtract i months
            month_year = (month_date.year * 12 + month_date.month - i - 1)
            y, m = divmod(month_year, 12)
            m += 1
            months.append({"year": y, "month": m})

        # Fetch data from DB
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    YEAR(created_at) AS year,
                    MONTH(created_at) AS month,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COUNT(*) AS invoice_count
                FROM invoices
                WHERE deleted_at IS NULL
                  AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY YEAR(created_at), MONTH(created_at)
                ORDER BY YEAR(created_at), MONTH(created_at)
                """
            )
            rows = cur.fetchall()

        # Map fetched data to months
        results = []
        for m in months:
            # Find matching row
            row = next(
                (r for r in rows if r["year"] == m["year"] and r["month"] == m["month"]),
                None
            )
            month_name = calendar.month_abbr[m["month"]]
            results.append({
                "month": f"{month_name} {m['year']}",
                "revenue": float(row["revenue"]) if row else 0.0,
                "invoice_count": int(row["invoice_count"]) if row else 0,
            })

        return results
    finally:
        conn.close()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    DATE_FORMAT(created_at, '%%Y-%%m') AS ym,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COUNT(*) AS invoice_count
                FROM invoices
                WHERE LOWER(status) = 'paid'
                  AND created_at >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
                GROUP BY ym
                ORDER BY ym ASC
                """
            )
            rows = cur.fetchall()

            # Create a mapping from "YYYY-MM" -> {"revenue": float, "count": int}
            stats_map = {
                row["ym"]: {
                    "revenue": float(row["revenue"]),
                    "count": int(row["invoice_count"])
                }
                for row in rows
            }

            today = datetime.today()
            results: List[Dict[str, Any]] = []

            # Generate last 6 months
            for i in range(5, -1, -1):
                year = today.year if today.month - i > 0 else today.year - 1
                month = (today.month - i - 1) % 12 + 1
                ym = f"{year}-{month:02d}"  # e.g., "2025-09"
                label = f"{calendar.month_abbr[month]} {year}"  # e.g., "Sep 2025"

                month_stats = stats_map.get(ym, {"revenue": 0.0, "count": 0})
                results.append({
                    "month": label,
                    "revenue": month_stats["revenue"],
                    "invoice_count": month_stats["count"],
                })

            return results
    finally:
        conn.close()
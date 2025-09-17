# =============================
# app/database/models/customer_model.py
# =============================
from marshmallow import ValidationError
from uuid6 import uuid7
from app.database.base import get_db_connection
from datetime import datetime
from typing import List

from app.utils.is_deleted_filter import is_deleted_filter
from app.utils.response import normalize_row, normalize_rows, normalize_value


def create_customer(full_name, email=None, phone=None, address=None, gst_number=None):
    conn = get_db_connection()
    customer_id = str(uuid7())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO customers (id, full_name, email, phone, address, gst_number)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (customer_id, full_name, email, phone, address, gst_number),
            )
        conn.commit()
    finally:
        conn.close()
    return get_customer(customer_id)


def get_customer(customer_id):
    deleted_sql, _ = is_deleted_filter("c")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT 
                    c.id AS id, 
                    c.full_name, 
                    c.email, 
                    c.phone,
                    c.address,
                    c.gst_number,
                    c.created_at, 
                    c.updated_at, 
                    CASE
                        WHEN COUNT(i.id) = 0 THEN 'New'
                        WHEN SUM(CASE WHEN i.status = 'Pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                        WHEN SUM(CASE WHEN i.status = 'Pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                        WHEN SUM(CASE WHEN i.status = 'Paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                        ELSE 'New'
                    END AS status
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                WHERE c.id=%s AND {deleted_sql}
                GROUP BY c.id, c.full_name, c.email, c.phone, c.address, c.gst_number
                """,
                (customer_id,),
            )
            customer = cur.fetchone()
    finally:
        conn.close()

    return normalize_row(customer) if customer else None


def list_customers(q=None, status=None, offset=0, limit=20):
    conn = get_db_connection()
    try:
        where, params = [], []

        # Always exclude deleted
        deleted_sql, deleted_params = is_deleted_filter("c")
        where.append(deleted_sql)
        params += deleted_params

        if q:
            where.append("(c.full_name LIKE %s OR c.email LIKE %s OR c.phone LIKE %s)")
            like = f"%{q}%"
            params += [like, like, like]

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        # Inner query: compute status
        base_query = f"""
            SELECT 
                c.id AS id,
                c.full_name, 
                c.email, 
                c.phone,
                c.address,
                c.gst_number,
                c.created_at, 
                c.updated_at,  
                CASE
                    WHEN COUNT(i.id) = 0 THEN 'New'
                    WHEN SUM(CASE WHEN i.status='Pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                    WHEN SUM(CASE WHEN i.status='Pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                    WHEN SUM(CASE WHEN i.status='Paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                    ELSE 'New'
                END AS status
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            {where_sql}
            GROUP BY c.id, c.full_name, c.email, c.phone, c.address, c.gst_number
        """

        # Outer query: filter by status
        outer_where = ""
        if status:
            outer_where = " WHERE sub.status = %s"
            params.append(status)

        final_query = f"""
            SELECT * FROM ({base_query}) AS sub
            {outer_where}
            ORDER BY sub.id DESC
            LIMIT %s OFFSET %s
        """

        with conn.cursor() as cur:
            cur.execute(final_query, (*params, limit, offset))
            rows = normalize_rows(list(cur.fetchall() or []))

            # Total count
            count_query = f"SELECT COUNT(*) AS total FROM ({base_query}) AS sub {outer_where}"
            cur.execute(count_query, tuple(params))
            result = cur.fetchone()
            total = normalize_value(result["total"]) if result else 0

    finally:
        conn.close()

    return rows, total


def update_customer(customer_id, **fields):
    if not fields:
        return get_customer(customer_id)

    keys = [f"{k}=%s" for k in fields]
    params = list(fields.values())
    params.append(customer_id)

    deleted_sql, _ = is_deleted_filter()
    sql = f"UPDATE customers SET {', '.join(keys)} WHERE id=%s AND {deleted_sql}"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            if cur.rowcount == 0:
                raise ValidationError("Customer does not exist or is deleted.")
        conn.commit()
    finally:
        conn.close()

    return get_customer(customer_id)


def bulk_delete_customers(ids: List[str]):
    if not ids:
        return 0

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            deleted_sql, _ = is_deleted_filter()
            sql = f"""
                UPDATE customers
                SET deleted_at=%s
                WHERE id IN ({placeholders}) AND {deleted_sql}
            """
            params = [datetime.now()] + ids
            cur.execute(sql, params)
            affected = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return affected


def customer_aggregates(customer_id):
    deleted_sql, _ = is_deleted_filter("c")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Total billed
            cur.execute(
                f"""
                SELECT COALESCE(SUM(i.total_amount), 0) AS total_billed
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                WHERE i.customer_id=%s AND {deleted_sql}
                """,
                (customer_id,),
            )
            billed = normalize_value((cur.fetchone() or {}).get("total_billed", 0))

            # Total paid
            cur.execute(
                f"""
                SELECT COALESCE(SUM(p.amount), 0) AS total_paid
                FROM payments p
                JOIN invoices i ON i.id = p.invoice_id
                JOIN customers c ON c.id = i.customer_id
                WHERE i.customer_id=%s AND {deleted_sql}
                """,
                (customer_id,),
            )
            paid = normalize_value((cur.fetchone() or {}).get("total_paid", 0))

            # Invoice history
            cur.execute(
                f"""
                SELECT 
                    i.id AS invoice_id,
                    i.invoice_number,
                    i.due_date,
                    i.total_amount,
                    i.status,
                    COALESCE(i.total_amount - (
                        SELECT COALESCE(SUM(p.amount), 0)
                        FROM payments p
                        WHERE p.invoice_id = i.id
                    ), i.total_amount) AS due_amount
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                WHERE i.customer_id=%s AND {deleted_sql}
                ORDER BY i.created_at DESC
                LIMIT 50
                """,
                (customer_id,),
            )
            history = normalize_rows(list(cur.fetchall() or []))

    finally:
        conn.close()

    return {
        "total_billed": billed,
        "total_paid": paid,
        "total_due": billed - paid,
        "invoices": history,
    }

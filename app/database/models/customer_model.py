# =============================
# app/database/models/customer_model.py
# =============================
from marshmallow import ValidationError
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_customer(
    full_name, email=None, phone=None, address=None, gst_number=None, status="active"
):
    conn = get_db_connection()
    customer_id = str(uuid7())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO customers (id, full_name, email, phone, address, gst_number, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (customer_id, full_name, email, phone, address, gst_number, status),
        )
    conn.commit()
    conn.close()
    return customer_id


def get_customer(customer_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE id=%s", (customer_id,))
        c = cur.fetchone()
    conn.close()
    return c


def list_customers(q=None, status=None, offset=0, limit=20):
    conn = get_db_connection()
    where, params = [], []
    if q:
        where.append("(full_name LIKE %s OR email LIKE %s OR phone LIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]
    if status:
        where.append("status=%s")
        params.append(status)
    where_sql = " WHERE " + " AND ".join(where) if where else ""

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT SQL_CALC_FOUND_ROWS * 
            FROM customers{where_sql} 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        rows = cur.fetchall()

        cur.execute("SELECT FOUND_ROWS() AS total")
        result = cur.fetchone()
        total = result["total"] if result else 0

    conn.close()
    return rows, total


def update_customer(customer_id, **fields):
    if not fields:
        return get_customer(customer_id)  # return existing data if no fields to update

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k}=%s")
        params.append(v)
    params.append(customer_id)
    sql = f"UPDATE customers SET {', '.join(keys)} WHERE id=%s"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            if cur.rowcount == 0:
                raise ValidationError(f"Customer does not exist.")
        conn.commit()
    finally:
        conn.close()
    return get_customer(customer_id)


def bulk_delete_customers(ids: list[str]):
    if not ids:
        return 0
    conn = get_db_connection()
    with conn.cursor() as cur:
        placeholders = ",".join(["%s"] * len(ids))
        cur.execute(f"DELETE FROM customers WHERE id IN ({placeholders})", ids)
        affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected


def customer_aggregates(customer_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Total billed
        cur.execute(
            """
            SELECT COALESCE(SUM(i.total_amount), 0) AS total_billed
            FROM invoices i 
            WHERE i.customer_id=%s
            """,
            (customer_id,),
        )
        billed = cur.fetchone()["total_billed"]

        # Total paid
        cur.execute(
            """
            SELECT COALESCE(SUM(p.amount), 0) AS total_paid
            FROM payments p 
            JOIN invoices i ON i.id = p.invoice_id
            WHERE i.customer_id=%s
            """,
            (customer_id,),
        )
        paid = cur.fetchone()["total_paid"]

        # Invoice history
        cur.execute(
            """
            SELECT id, invoice_number, due_date, total_amount, status
            FROM invoices 
            WHERE customer_id=%s 
            ORDER BY created_at DESC 
            LIMIT 50
            """,
            (customer_id,),
        )
        history = cur.fetchall()

    conn.close()
    return {
        "total_billed": float(billed),
        "total_paid": float(paid),
        "total_due": float(billed - paid),
        "invoices": history,
    }

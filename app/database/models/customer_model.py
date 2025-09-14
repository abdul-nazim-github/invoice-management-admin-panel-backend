# =============================
# app/database/models/customer_model.py
# =============================
from marshmallow import ValidationError
from uuid6 import uuid7
from app.database.base import get_db_connection
from datetime import datetime


def create_customer(
    full_name, email=None, phone=None, address=None, gst_number=None,
):
    conn = get_db_connection()
    customer_id = str(uuid7())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO customers (id, full_name, email, phone, address, gst_number)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (customer_id, full_name, email, phone, address, gst_number),
        )
    conn.commit()
    conn.close()
    return get_customer(customer_id)


def get_customer(customer_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 
                c.id, 
                c.full_name, 
                c.email, 
                c.phone, 
                CASE
                    WHEN COUNT(i.id) = 0 THEN 'New'
                    WHEN SUM(CASE WHEN i.status = 'pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                    WHEN SUM(CASE WHEN i.status = 'pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                    WHEN SUM(CASE WHEN i.status = 'paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                    ELSE 'New'
                END AS status
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            WHERE c.id = %s
            GROUP BY c.id
            """,
            (customer_id,)
        )
        c = cur.fetchone()
    conn.close()
    return c

def list_customers(q=None, status=None, offset=0, limit=20):
    conn = get_db_connection()
    where, params = [], []

    # Search filter
    if q:
        where.append("(c.full_name LIKE %s OR c.email LIKE %s OR c.phone LIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]

    # Build dynamic query with computed status
    query = f"""
        SELECT 
            c.id, 
            c.full_name, 
            c.email, 
            c.phone, 
            -- Compute customer status from invoices
            CASE
                WHEN COUNT(i.id) = 0 THEN 'New'
                WHEN SUM(CASE WHEN i.status = 'pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                WHEN SUM(CASE WHEN i.status = 'pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                WHEN SUM(CASE WHEN i.status = 'paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                ELSE 'New'
            END AS status
        FROM customers c
        LEFT JOIN invoices i ON c.id = i.customer_id
    """

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    query += where_sql + " GROUP BY c.id ORDER BY c.created_at DESC LIMIT %s OFFSET %s"

    with conn.cursor() as cur:
        cur.execute(query, (*params, limit, offset))
        rows = cur.fetchall()

        # For total count (without LIMIT/OFFSET)
        count_query = f"""
            SELECT COUNT(*) as total
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            {where_sql}
            GROUP BY c.id
        """
        cur.execute(f"SELECT COUNT(*) as total FROM ({count_query}) as sub", tuple(params))
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
    keys.append("updated_at=%s")
    params.append(datetime.now())  # current timestamp
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
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            sql = f"""
                UPDATE customers
                SET deleted_at = %s
                WHERE id IN ({placeholders})
            """
            # First parameter is current timestamp, followed by ids
            params = [datetime.now()] + ids
            cur.execute(sql, params)
            affected = cur.rowcount

        conn.commit()
        return affected
    finally:
        conn.close()


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

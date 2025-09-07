# =============================
# app/database/models/invoice_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_invoice(
    invoice_number,
    customer_id,
    due_date,
    tax_percent,
    discount,
    total_amount,
    status,
):
    conn = get_db_connection()
    invoice_id = str(uuid7())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO invoices
            (id, invoice_number, customer_id, tax_percent, discount, total_amount, status, due_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                invoice_id,
                invoice_number,
                customer_id,
                tax_percent,
                discount,
                total_amount,
                status,
                due_date,
            ),
        )
    conn.commit()
    conn.close()
    return invoice_id


def get_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM invoices WHERE id=%s", (invoice_id,))
        inv = cur.fetchone()
    conn.close()
    return inv


def list_invoices(q=None, status=None, offset=0, limit=20):
    conn = get_db_connection()
    where, params = [], []
    if q:
        like = f"%{q}%"
        where.append("(invoice_number LIKE %s)")
        params += [like]
    if status:
        where.append("status=%s")
        params.append(status)
    where_sql = " WHERE " + " AND ".join(where) if where else ""

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT SQL_CALC_FOUND_ROWS * FROM invoices{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        rows = cur.fetchall()
        cur.execute("SELECT FOUND_ROWS() AS total")
        result = cur.fetchone()
        total = result["total"] if result else 0
    conn.close()
    return rows, total


def update_invoice(invoice_id, **fields):
    if not fields:
        return
    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k}=%s")
        params.append(v)
    params.append(invoice_id)
    sql = f"UPDATE invoices SET {', '.join(keys)} WHERE id=%s"
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
    conn.commit()
    conn.close()


def bulk_delete_invoices(ids: list[int]):
    if not ids:
        return 0
    conn = get_db_connection()
    with conn.cursor() as cur:
        placeholders = ",".join(["%s"] * len(ids))
        cur.execute(f"DELETE FROM invoices WHERE id IN ({placeholders})", ids)
        affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected

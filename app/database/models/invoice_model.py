# =============================
# app/database/models/invoice_model.py
# =============================
from app.database.base import get_db_connection


def create_invoice(invoice_number, customer_id, user_id, invoice_date, due_date, total_amount, status="unpaid"):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO invoices (invoice_number, customer_id, user_id, invoice_date, due_date, total_amount, status)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (invoice_number, customer_id, user_id, invoice_date, due_date, total_amount, status)
        )
        iid = cur.lastrowid
    conn.commit()
    conn.close()
    return iid


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
        cur.execute(f"SELECT SQL_CALC_FOUND_ROWS * FROM invoices{where_sql} ORDER BY invoice_date DESC LIMIT %s OFFSET %s",
                    (*params, limit, offset))
        rows = cur.fetchall()
        cur.execute("SELECT FOUND_ROWS() AS total")
        total = cur.fetchone()["total"]
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

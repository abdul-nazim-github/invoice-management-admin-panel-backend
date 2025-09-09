# =============================
# app/database/models/invoice_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_invoice(
    conn,
    invoice_number: str,
    customer_id: str,
    due_date: str,
    tax_percent: float,
    discount_amount: float,
    total_amount: float,
    status: str,
) -> str:
    """
    Create a new invoice. Uses the existing connection (transaction safe).
    """
    invoice_id = str(uuid7())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO invoices (
                id, invoice_number, customer_id,
                tax_percent, discount_amount, total_amount,
                status, due_date
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                invoice_id,
                invoice_number,
                customer_id,
                tax_percent,
                discount_amount,
                total_amount,
                status,
                due_date,
            ),
        )
    return invoice_id


def get_invoice(invoice_id: str):
    """
    Get invoice details with joined customer info.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    i.id,
                    i.invoice_number,
                    i.created_at,
                    i.due_date,
                    i.tax_percent,
                    i.discount_amount,
                    i.total_amount,
                    i.status,
                    c.id AS customer_id,
                    c.full_name AS customer_full_name,
                    c.email AS customer_email,
                    c.phone AS customer_phone,
                    c.address AS customer_address,
                    c.gst_number AS customer_gst
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                WHERE i.id = %s
                """,
                (invoice_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def list_invoices(q: str = '', status: str = '', offset: int = 0, limit: int = 20):
    """
    Paginated list of invoices with optional search & status filter.
    """
    conn = get_db_connection()
    where, params = [], []

    if q:
        like = f"%{q}%"
        where.append("(i.invoice_number LIKE %s OR c.full_name LIKE %s)")
        params += [like, like]

    if status:
        where.append("i.status = %s")
        params.append(status)

    where_sql = f" WHERE {' AND '.join(where)}" if where else ""

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT SQL_CALC_FOUND_ROWS 
                    i.id,
                    i.invoice_number,
                    c.full_name AS customer_full_name,
                    i.created_at,
                    i.total_amount,
                    i.status
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                {where_sql}
                ORDER BY i.created_at DESC 
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()

            cur.execute("SELECT FOUND_ROWS() AS total")
            result = cur.fetchone()
            total = result["total"] if result else 0

        return rows, total
    finally:
        conn.close()


def update_invoice(invoice_id: str, **fields) -> bool:
    """
    Update invoice fields dynamically.
    """
    if not fields:
        return False

    keys = [f"{k}=%s" for k in fields.keys()]
    params = list(fields.values()) + [invoice_id]
    sql = f"UPDATE invoices SET {', '.join(keys)} WHERE id=%s"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
        conn.commit()
        return True
    finally:
        conn.close()


def bulk_delete_invoices(ids: list[str]) -> int:
    """
    Delete multiple invoices by IDs.
    """
    if not ids:
        return 0

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(f"DELETE FROM invoices WHERE id IN ({placeholders})", ids)
            affected = cur.rowcount
        conn.commit()
        return affected
    finally:
        conn.close()

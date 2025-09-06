# =============================
# app/database/models/payment_model.py
# =============================
from app.database.base import get_db_connection


def create_payment(invoice_id, amount, payment_date, method, reference_no=None):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO payments (invoice_id, amount, payment_date, method, reference_no) VALUES (%s,%s,%s,%s,%s)",
            (invoice_id, amount, payment_date, method, reference_no)
        )
    conn.commit()
    conn.close()


def sum_payments_for_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(amount),0) AS paid FROM payments WHERE invoice_id=%s", (invoice_id,))
        paid = cur.fetchone()["paid"]
    conn.close()
    return float(paid)

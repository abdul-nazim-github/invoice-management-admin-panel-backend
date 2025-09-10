# =============================
# app/database/models/payment_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_payment(invoice_id: str, amount: float, method: str = "cash", reference_number: str = '') -> str:
    """
    Create a new payment for an invoice.
    `paid_at` is auto-filled by DB.
    """
    conn = get_db_connection()
    try:
        payment_id = str(uuid7())
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payments (id, invoice_id, amount, method, reference_number)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (payment_id, invoice_id, amount, method, reference_number),
            )
        conn.commit()
        return payment_id
    finally:
        conn.close()


def get_payments_by_invoice(invoice_id: str) -> float:
    """
    Get the total paid amount for a given invoice.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT SUM(amount) AS total_paid
                FROM payments
                WHERE invoice_id = %s
                """,
                (invoice_id,),
            )
            result = cursor.fetchone()
            total_paid = float(result["total_paid"]) if result and result["total_paid"] else 0.0
        return total_paid
    finally:
        conn.close()
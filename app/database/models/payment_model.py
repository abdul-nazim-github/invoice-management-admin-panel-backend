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


def get_payments_by_invoice(invoice_id: str):
    """
    Get all payments for a given invoice.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, invoice_id, amount, method, reference_number, paid_at
                FROM payments
                WHERE invoice_id = %s
                ORDER BY paid_at DESC
                """,
                (invoice_id,),
            )
            payments = cursor.fetchall()
        return payments
    finally:
        conn.close()

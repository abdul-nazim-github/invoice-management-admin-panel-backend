# =============================
# app/database/models/payment_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


from uuid6 import uuid7

def create_payment(
    invoice_id: str,
    amount: float,
    payment_date: str | None = None,
    method: str = "cash",
    reference_number: str = ""
) -> str:
    """
    Create a new payment for an invoice.
    - `paid_at` auto-filled by DB unless `payment_date` is given.
    """
    conn = get_db_connection()
    try:
        payment_id = str(uuid7())
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payments (id, invoice_id, amount, method, reference_number, paid_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    payment_id,
                    invoice_id,
                    amount,
                    method,
                    reference_number,
                    payment_date,  # ✅ allow override, else DB default
                ),
            )
        conn.commit()
        return payment_id
    finally:
        conn.close()


def get_payments_by_invoice(invoice_id: str) -> float:
    """
    Get total paid amount for a given invoice.
    Returns 0.0 if no payments found.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total_paid
                FROM payments
                WHERE invoice_id = %s
                """,
                (invoice_id,),
            )
            row = cursor.fetchone()
            return float(row["total_paid"]) if row else 0.0
    finally:
        conn.close()

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
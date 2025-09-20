# =============================
# app/database/models/payment_model.py
# =============================
from decimal import Decimal
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_payment(
    invoice_id: str,
    amount: Decimal,
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
                    amount,  # Decimal supported by PyMySQL
                    method,
                    reference_number,
                    payment_date,  # override DB default if provided
                ),
            )
        conn.commit()
        return payment_id
    finally:
        conn.close()


def get_payments_by_invoice(invoice_id: str) -> Decimal:
    """
    Get total paid amount for a given invoice.
    Returns Decimal('0.00') if no payments found.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total_paid
                FROM payments
                WHERE invoice_id = %s
                """,
                (invoice_id,),
            )
            row = cursor.fetchone()
            total_paid = row["total_paid"] if row and row["total_paid"] is not None else 0
            return Decimal(str(total_paid)).quantize(Decimal("0.01"))
    finally:
        conn.close()

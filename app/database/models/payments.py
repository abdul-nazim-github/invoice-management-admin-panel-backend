from .base import get_db_connection

def create_payment(invoice_id, amount, payment_date, method, reference_no=None):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO payments (invoice_id, amount, payment_date, method, reference_no) VALUES (%s, %s, %s, %s, %s)",
            (invoice_id, amount, payment_date, method, reference_no)
        )
    conn.commit()
    conn.close()

def get_payments_by_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM payments WHERE invoice_id = %s", (invoice_id,))
        payments = cursor.fetchall()
    conn.close()
    return payments

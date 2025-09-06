from .base import get_db_connection

def add_invoice_item(invoice_id, product_id, quantity, price, total):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO invoice_items (invoice_id, product_id, quantity, price, total) VALUES (%s, %s, %s, %s, %s)",
            (invoice_id, product_id, quantity, price, total)
        )
    conn.commit()
    conn.close()

def get_items_by_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
        items = cursor.fetchall()
    conn.close()
    return items

def delete_items_by_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
    conn.commit()
    conn.close()

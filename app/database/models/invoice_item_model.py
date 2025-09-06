# =============================
# app/database/models/invoice_item_model.py
# =============================
from app.database.base import get_db_connection


def add_invoice_item(invoice_id, product_id, quantity, price):
    total = float(price) * int(quantity)
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO invoice_items (invoice_id, product_id, quantity, price, total) VALUES (%s,%s,%s,%s,%s)",
            (invoice_id, product_id, quantity, price, total)
        )
    conn.commit()
    conn.close()


def get_items_by_invoice(invoice_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ii.*, p.name, p.product_code
            FROM invoice_items ii
            JOIN products p ON p.id=ii.product_id
            WHERE ii.invoice_id=%s
            """,
            (invoice_id,)
        )
        items = cur.fetchall()
    conn.close()
    return items
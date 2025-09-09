# =============================
# app/database/models/invoice_item_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


def add_invoice_item(conn, invoice_id, product_id, quantity, unit_price):
    """
    Add an invoice item and deduct stock.
    Must be called inside a transaction (conn passed in).
    Does NOT commit/rollback/close — caller controls that.
    """
    total_amount = float(unit_price) * int(quantity)
    invoice_item_id = str(uuid7())

    with conn.cursor() as cur:
        # 1️⃣ Deduct stock first (atomic check)
        cur.execute(
            """
            UPDATE products 
            SET stock_quantity = stock_quantity - %s 
            WHERE id = %s AND stock_quantity >= %s
            """,
            (quantity, product_id, quantity),
        )

        # 2️⃣ If no rows updated → not enough stock
        if cur.rowcount == 0:
            raise ValueError(f"Product {product_id} is out of stock.")

        # 3️⃣ Insert invoice item only after stock deduction success
        cur.execute(
            """
            INSERT INTO invoice_items 
            (id, invoice_id, product_id, quantity, unit_price, total_amount) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                invoice_item_id,
                invoice_id,
                product_id,
                quantity,
                unit_price,
                total_amount,
            ),
        )

    return invoice_item_id


def get_items_by_invoice(invoice_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    ii.id,
                    ii.quantity,
                    ii.unit_price,
                    ii.total_amount,
                    p.id AS product_id,
                    p.name AS product_name,
                    p.sku AS product_sku,
                    p.unit_price AS product_unit_price
                FROM invoice_items ii
                JOIN products p ON p.id = ii.product_id
                WHERE ii.invoice_id = %s
                """,
                (invoice_id,),
            )
            items = cur.fetchall()
        return items
    finally:
        conn.close()

# =============================
# app/database/models/invoice_item_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection
from app.utils.exceptions.exception import OutOfStockError


def add_invoice_item(invoice_id, product_id, quantity, price):
    total_amount = float(price) * int(quantity)
    conn = get_db_connection()
    invoice_item_id = str(uuid7())

    try:
        with conn.cursor() as cur:
            # 1️⃣ Deduct stock first (atomic check)
            cur.execute(
                """
                UPDATE products 
                SET stock = stock - %s 
                WHERE id = %s AND stock >= %s
                """,
                (quantity, product_id, quantity),
            )

            # 2️⃣ If no rows updated → not enough stock
            if cur.rowcount == 0:
                raise OutOfStockError(product_id)

            # 3️⃣ Insert invoice item only after stock deduction success
            cur.execute(
                """
                INSERT INTO invoice_items 
                (id, invoice_id, product_id, quantity, price, total_amount) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    invoice_item_id,
                    invoice_id,
                    product_id,
                    quantity,
                    price,
                    total_amount,
                ),
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return invoice_item_id


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
            (invoice_id,),
        )
        items = cur.fetchall()
    conn.close()
    return items

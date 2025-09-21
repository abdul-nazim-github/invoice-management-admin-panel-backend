# =============================
# app/database/models/invoice_item_model.py
# =============================
from uuid6 import uuid7
from decimal import Decimal
from app.database.base import get_db_connection
from marshmallow import ValidationError

from app.utils.response import normalize_rows


def add_invoice_item(conn, invoice_id, product_id, quantity, unit_price):
    """
    Add an invoice item and deduct stock.
    Must be called inside a transaction (conn passed in).
    Raises ValidationError if stock is insufficient.
    """
    quantity = int(quantity)
    unit_price = Decimal(str(unit_price))
    total_amount = (unit_price * quantity).quantize(Decimal("0.01"))

    invoice_item_id = str(uuid7())

    with conn.cursor() as cur:
        # Deduct stock atomically
        cur.execute(
            """
            UPDATE products 
            SET stock_quantity = stock_quantity - %s 
            WHERE id = %s AND stock_quantity >= %s
            """,
            (quantity, product_id, quantity),
        )

        if cur.rowcount == 0:
            raise ValidationError(
                {"product_id": [f"Product {product_id} is out of stock"]}
            )

        # Insert invoice item
        cur.execute(
            """
            INSERT INTO invoice_items 
            (id, invoice_id, product_id, quantity, unit_price, total_amount) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (invoice_item_id, invoice_id, product_id, quantity, unit_price, total_amount),
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
                    ii.quantity as ordered_quantity,
                    CAST(ii.unit_price AS DECIMAL(10,2)) AS unit_price,
                    CAST(ii.total_amount AS DECIMAL(10,2)) AS total_amount,
                    p.id AS product_id,
                    p.name AS name,
                    p.sku AS sku,
                    p.stock_quantity as stock_quantity
                FROM invoice_items ii
                JOIN products p ON p.id = ii.product_id
                WHERE ii.invoice_id = %s
                """,
                (invoice_id,),
            )
            items = cur.fetchall()

            # Convert numeric fields to Decimal
            for it in items:
                it["unit_price"] = Decimal(str(it["unit_price"]))
                it["total_amount"] = Decimal(str(it["total_amount"]))

        return normalize_rows(items)
    finally:
        conn.close()

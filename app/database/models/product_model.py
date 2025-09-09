# =============================
# app/database/models/product_model.py
# =============================
from datetime import datetime
from marshmallow import ValidationError
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_product(sku, name, description, unit_price, stock_quantity, status="active"):
    conn = get_db_connection()
    pid = str(uuid7())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO products (id, sku, name, description, unit_price, stock_quantity, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (pid, sku, name, description, unit_price, stock_quantity, status),
        )
    conn.commit()
    conn.close()
    return pid


def list_products(q=None, status=None, offset=0, limit=20):
    conn = get_db_connection()
    where, params = [], []
    if q:
        like = f"%{q}%"
        where.append("(name LIKE %s OR sku LIKE %s)")
        params += [like, like]
    if status:
        where.append("status=%s")
        params.append(status)
    where_sql = " WHERE " + " AND ".join(where) if where else ""

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT SQL_CALC_FOUND_ROWS * 
            FROM products{where_sql} 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        rows = cur.fetchall()

        cur.execute("SELECT FOUND_ROWS() AS total")
        total = cur.fetchone()["total"]

    conn.close()
    return rows, total


def get_product(product_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
        prod = cur.fetchone()
    conn.close()
    return prod

def update_product(product_id, **fields):
    if not fields:
        return get_product(product_id)  # return existing data if no fields to update

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k}=%s")
        params.append(v)
    keys.append("updated_at=%s")
    params.append(datetime.now())  # current timestamp
    params.append(product_id)
    sql = f"UPDATE products SET {', '.join(keys)} WHERE id=%s"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            if cur.rowcount == 0:
                raise ValidationError(f"Product does not exist.")
        conn.commit()
    finally:
        conn.close()
    return get_product(product_id)

def bulk_delete_products(ids: list[str]):
    if not ids:
        return 0

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            sql = f"""
                UPDATE products
                SET deleted_at = %s
                WHERE id IN ({placeholders})
            """
            # First parameter is current timestamp, followed by ids
            params = [datetime.now()] + ids
            cur.execute(sql, params)
            affected = cur.rowcount

        conn.commit()
        return affected
    finally:
        conn.close()

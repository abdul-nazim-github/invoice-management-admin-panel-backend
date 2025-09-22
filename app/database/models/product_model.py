# =============================
# app/database/models/product_model.py
# =============================
from datetime import datetime
from decimal import Decimal
from marshmallow import ValidationError
from uuid6 import uuid7
from typing import List
from app.database.base import get_db_connection
from app.utils.is_deleted_filter import is_deleted_filter
from app.utils.response import normalize_rows, normalize_value
from app.utils.utils import generate_unique_sku

# -------------------------
# Product CRUD
# -------------------------

def create_product(name, description, unit_price, stock_quantity):
    conn = get_db_connection()
    product_id = str(uuid7())
    sku = generate_unique_sku(name)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (id, sku, name, description, unit_price, stock_quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    product_id,
                    sku,
                    name,
                    description,
                    Decimal(str(unit_price)),  # Ensure Decimal
                    int(stock_quantity)
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return get_product(product_id)


def list_products(q=None, offset=0, limit=20):
    conn = get_db_connection()
    where, params = [], []

    if q:
        like = f"%{q}%"
        where.append("(name LIKE %s OR sku LIKE %s)")
        params += [like, like]

    deleted_sql, _ = is_deleted_filter()
    where.append(deleted_sql)

    where_sql = " WHERE " + " AND ".join(where) if where else ""

    try:
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
            rows = cur.fetchall() or []

            # Total count
            cur.execute("SELECT FOUND_ROWS() AS total")
            total_row = cur.fetchone()
            total = normalize_value(total_row["total"]) if total_row else 0

    finally:
        conn.close()

    # Convert unit_price to Decimal
    for row in rows:
        if "unit_price" in row and row["unit_price"] is not None:
            row["unit_price"] = Decimal(str(row["unit_price"]))

    return normalize_rows(rows), total


def get_product(product_id):
    conn = get_db_connection()
    deleted_sql, _ = is_deleted_filter()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM products WHERE id=%s AND {deleted_sql}",
                (product_id,)
            )
            prod = cur.fetchone()
            prod = normalize_rows([prod])[0] if prod else None
    finally:
        conn.close()

    if prod and "unit_price" in prod and prod["unit_price"] is not None:
        prod["unit_price"] = Decimal(str(prod["unit_price"]))

    return prod


def update_product(product_id, **fields):
    if not fields:
        return get_product(product_id)

    keys, params = [], []
    for k, v in fields.items():
        if k == "unit_price":
            v = Decimal(str(v))
        elif k == "stock_quantity":
            v = int(v)
        keys.append(f"{k}=%s")
        params.append(v)

    keys.append("updated_at=%s")
    params.append(datetime.now())

    deleted_sql, _ = is_deleted_filter()
    sql = f"UPDATE products SET {', '.join(keys)} WHERE id=%s AND {deleted_sql}"
    params.append(product_id)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            if cur.rowcount == 0:
                raise ValidationError("Product does not exist or is deleted.")
        conn.commit()
    finally:
        conn.close()

    return get_product(product_id)


def bulk_delete_products(ids: List[str]):
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
            params = [datetime.now()] + ids
            cur.execute(sql, params)
            affected = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return affected

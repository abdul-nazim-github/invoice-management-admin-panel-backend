# =============================
# app/database/models/invoice_model.py
# =============================
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from marshmallow import ValidationError
from uuid6 import uuid7
from app.database.base import get_db_connection
from app.database.models.invoice_item_model import add_invoice_item, get_items_by_invoice
from app.database.models.payment_model import get_payments_by_invoice
from app.database.models.product_model import get_product
from app.utils.response import normalize_row, normalize_rows, normalize_value
from app.utils.utils import generate_invoice_number

# ---------------- Invoice Functions ----------------
def create_invoice(
    conn,
    customer_id: str,
    due_date: str,
    tax_percent: Decimal,
    tax_amount: Decimal,
    discount_amount: Decimal,
    subtotal_amount: Decimal,
    total_amount: Decimal,
    amount_paid: Decimal = Decimal("0.0"),
) -> str:
    invoice_id = str(uuid7())
    invoice_number = generate_invoice_number(conn, customer_id)
    status = "Paid" if amount_paid >= total_amount else "Pending"

    with conn.cursor() as cur:
        # ---------- Insert Invoice ----------
        cur.execute(
            """
            INSERT INTO invoices (
                id, invoice_number, customer_id,
                tax_percent, tax_amount, discount_amount, subtotal_amount, 
                total_amount, status, due_date
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                invoice_id,
                invoice_number,
                customer_id,
                tax_percent,
                tax_amount,
                discount_amount,
                subtotal_amount, 
                total_amount, 
                status,
                due_date,
            ),
        )

        # ---------- Insert Payment if amount_paid > 0 ----------
        if amount_paid > Decimal("0.0"):
            payment_id = str(uuid7())
            cur.execute(
                """
                INSERT INTO payments (
                    id, invoice_id, amount, method
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    payment_id,
                    invoice_id,
                    amount_paid,
                    "cash",
                ),
            )

    return invoice_id

def get_invoice(invoice_id: str) -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    i.id,
                    i.invoice_number,
                    i.created_at,
                    i.updated_at,
                    i.due_date,
                    i.tax_percent,
                    i.discount_amount,
                    i.subtotal_amount,
                    i.total_amount,
                    i.status,
                    c.id AS customer_id,
                    c.full_name AS ull_name,
                    c.email AS email,
                    c.phone AS phone,
                    c.address AS address,
                    c.gst_number AS gst_number
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                WHERE i.id = %s
                """,
                (invoice_id,),
            )
            row = cur.fetchone()
            if row:
                # Convert Decimal fields to float for JSON response
                for field in ["tax_percent", "discount_amount", "subtotal_amount", "total_amount"]:
                    if row[field] is not None:
                        row[field] = float(row[field])
            return normalize_row(row) if row else None
    finally:
        conn.close()

def list_invoices(q=None, status=None, offset=0, limit=20, before=None, after=None):
    conn = get_db_connection()
    where, params = [], []

    if q:
        like = f"%{q}%"
        where.append("(i.invoice_number LIKE %s OR c.full_name LIKE %s)")
        params += [like, like]

    if status:
        where.append("i.status = %s")
        params.append(status)

    if before:
        where.append("i.created_at < %s")
        params.append(before)

    if after:
        where.append("i.created_at > %s")
        params.append(after)

    where_sql = f" WHERE {' AND '.join(where)}" if where else ""

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT SQL_CALC_FOUND_ROWS 
                    i.id,
                    i.invoice_number,
                    c.full_name AS customer_full_name,
                    i.created_at,
                    i.updated_at,
                    i.total_amount,
                    i.status
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                {where_sql}
                ORDER BY i.created_at DESC 
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = normalize_rows(cur.fetchall())

            # Convert total_amount to Decimal
            for r in rows:
                r["total_amount"] = Decimal(str(r["total_amount"]))

            cur.execute("SELECT FOUND_ROWS() AS total")
            result = cur.fetchone()
            total = normalize_value(result["total"]) if result else 0

        return rows, total
    finally:
        conn.close()

def update_invoice(invoice_id: str, **fields) -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM invoices WHERE id=%s", (invoice_id,))
            existing = cur.fetchone()
            if not existing:
                return None

        items = fields.pop("items", None)
        subtotal = Decimal("0.0")

        if items is not None:
            for it in items:
                prod = get_product(it["product_id"])
                if not prod:
                    conn.rollback()
                    raise ValidationError(
                        {"product_id": [f"Product {it['product_id']} does not exist"]}
                    )

                quantity = Decimal(it.get("quantity", 1))
                unit_price = Decimal(str(prod["unit_price"]))
                line_total = (quantity * unit_price).quantize(Decimal("0.01"))

                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM invoice_items WHERE invoice_id=%s AND product_id=%s",
                        (invoice_id, it["product_id"]),
                    )
                    existing_item = cur.fetchone()

                    if existing_item:
                        cur.execute(
                            """
                            UPDATE invoice_items
                            SET quantity=%s, unit_price=%s, total_amount=%s, updated_at=%s
                            WHERE id=%s
                            """,
                            (quantity, unit_price, line_total, datetime.now(), existing_item["id"]),
                        )
                    else:
                        add_invoice_item(conn, invoice_id, it["product_id"], quantity, unit_price)

                subtotal += line_total
        else:
            db_items = get_items_by_invoice(invoice_id)
            subtotal = sum(
                Decimal(str(it["unit_price"])) * Decimal(str(it["quantity"]))
                for it in db_items
            ).quantize(Decimal("0.01"))

        tax_percent = Decimal(str(fields.get("tax_percent", existing.get("tax_percent") or 0)))
        discount_amount = Decimal(str(fields.get("discount_amount", existing.get("discount_amount") or 0)))
        tax_amount = (subtotal * tax_percent / Decimal("100")).quantize(Decimal("0.01"))
        total = (subtotal + tax_amount - discount_amount).quantize(Decimal("0.01"))

        update_fields = {
            **fields,
            "tax_percent": tax_percent,
            "discount_amount": discount_amount,
            "total_amount": total,
            "updated_at": datetime.now(),
        }

        if update_fields:
            keys = [f"{k}=%s" for k in update_fields.keys()]
            sql = f"UPDATE invoices SET {', '.join(keys)} WHERE id=%s"
            params = list(update_fields.values()) + [invoice_id]

            with conn.cursor() as cur:
                cur.execute(sql, params)

        conn.commit()
        return get_invoice_detail(invoice_id)

    finally:
        conn.close()

def bulk_delete_invoices(ids: list[str]):
    if not ids:
        return 0

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            sql = f"""
                UPDATE invoices
                SET deleted_at = %s
                WHERE id IN ({placeholders})
            """
            params = [datetime.now()] + ids
            cur.execute(sql, params)
            affected = cur.rowcount

        conn.commit()
        return affected
    finally:
        conn.close()

def get_invoice_detail(invoice_id: str):
    inv = get_invoice(invoice_id)
    if not inv:
        return None

    items = get_items_by_invoice(invoice_id)
    paid = get_payments_by_invoice(invoice_id)
    due = (Decimal(str(inv["total_amount"])) - Decimal(str(paid))).quantize(Decimal("0.01"))

    return {
        "customer": {
            "id": inv["customer_id"],
            "full_name": inv["customer_full_name"],
            "email": inv["customer_email"],
            "phone": inv["customer_phone"],
            "address": inv["customer_address"],
        },
        "invoice": {
            "id": inv["id"],
            "invoice_number": inv["invoice_number"],
            "created_at": inv["created_at"],
            "updated_at": inv["updated_at"],
            "due_date": inv["due_date"],
            "status": inv["status"],
            "tax_percent": inv["tax_percent"],
            "discount_amount": inv["discount_amount"],
            "total_amount": inv["total_amount"],
            "paid_amount": paid,
            "due_amount": due,
        },
        "items": normalize_rows(items),
    }

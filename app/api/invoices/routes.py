# =============================
# app/api/invoices/routes.py
# =============================
from datetime import date
from typing import Any, Dict
from flask import Blueprint, request
from marshmallow import ValidationError
from pymysql.err import IntegrityError

from app.api.invoices.payment_schemas import PaymentCreateSchema
from app.api.invoices.schemas import (
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    InvoiceBulkDeleteSchema,
    InvoiceFilterSchema,
)
from app.database.base import get_db_connection
from app.utils.auth import require_auth
from app.utils.pagination import get_pagination
from app.utils.response import error_response, success_response
from app.database.models.invoice_model import (
    create_invoice,
    get_invoice,
    list_invoices,
    update_invoice,
    bulk_delete_invoices,
)
from app.database.models.invoice_item_model import (
    add_invoice_item,
    get_items_by_invoice,
)
from app.database.models.product_model import get_product
from app.database.models.payment_model import create_payment, get_payments_by_invoice


invoices_bp = Blueprint("invoices", __name__)

# schemas
create_schema = InvoiceCreateSchema()
update_schema = InvoiceUpdateSchema()
bulk_delete_schema = InvoiceBulkDeleteSchema()
filter_schema = InvoiceFilterSchema()
payment_schema = PaymentCreateSchema()


@invoices_bp.post("/")
@require_auth
def add_invoice():
    try:
        conn = get_db_connection()
        data = request.json or {}
        validated: Dict[str, Any] = create_schema.load(data)
        items: list[Dict[str, Any]] = validated.get("items", [])

        # ---------- Calculate subtotal ----------
        subtotal = 0.0
        for it in items:
            prod = get_product(it["product_id"])
            if not prod:
                return error_response(
                    type="invalid_product",
                    message="Invalid product",
                    details={"product_id": [f"Product {it['product_id']} does not exist"]},
                    status=400,
                )
            subtotal += float(prod["unit_price"]) * int(it.get("quantity", 1))

        tax_percent = float(validated.get("tax_percent", 0))
        discount_amount = float(validated.get("discount_amount", 0))
        tax_amount = subtotal * (tax_percent / 100)
        total = subtotal + tax_amount - discount_amount

        # ---------- Create invoice ----------
        try:
            invoice_id = create_invoice(
                conn,
                validated["invoice_number"],
                validated["customer_id"],
                validated["due_date"],
                tax_percent,
                discount_amount,
                total,
                validated.get("status", "Pending"),
            )
        except IntegrityError as ie:
            msg = str(ie)
            if "FOREIGN KEY (`customer_id`) REFERENCES `customers`" in msg:
                return error_response(
                    type="invalid_customer",
                    message="Invalid customer",
                    details={"customer_id": ["Customer does not exist"]},
                    status=400,
                )
            if "Duplicate entry" in msg:
                return error_response(
                    type="duplicate_entry",
                    message="Duplicate invoice number",
                    details={"invoice_number": ["Invoice number already exists"]},
                    status=409,
                )
            return error_response(
                type="integrity_error",
                message="Integrity Error",
                details={"error": [msg]},
                status=400,
            )

        # ---------- Add invoice items ----------
        for it in items:
            prod = get_product(it["product_id"])
            add_invoice_item(
                conn,
                invoice_id,
                it["product_id"],
                it.get("quantity", 1),
                prod["unit_price"],  # type: ignore
            )

        conn.commit()
        return success_response(
            result={"id": invoice_id},
            message="Invoice created successfully",
            status=201,
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )

    finally:
        conn.close()


@invoices_bp.get("/")
@require_auth
def list_invoices_route():
    try:
        args = request.args or {}
        validated: Dict[str, Any] = filter_schema.load(args)

        page, limit, offset = get_pagination()
        before = args.get("before")
        after = args.get("after")

        rows, total = list_invoices(
            q=validated.get("q"),
            status=validated.get("status"),
            offset=offset,
            limit=limit,
            before=before,
            after=after,
        )

        # enrich each invoice with paid and due amounts
        for inv in rows:
            paid = get_payments_by_invoice(inv["id"])
            inv["paid_amount"] = paid
            inv["due_amount"] = float(inv["total_amount"]) - paid

        meta = {"page": page, "limit": limit, "total": total}
        if before or after:
            meta["cursor_mode"] = True
            if rows:
                meta["first_created_at"] = rows[0]["created_at"]
                meta["last_created_at"] = rows[-1]["created_at"]

        return success_response(
            result=rows,
            message="Invoices fetched successfully",
            meta=meta,
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@invoices_bp.get("/<invoice_id>")
@require_auth
def detail(invoice_id):
    try:
        inv = get_invoice(invoice_id)
        if not inv:
            return error_response(
                type="not_found",
                message="Invoice does not exist",
                details=[],
                status=400,
            )

        items = get_items_by_invoice(invoice_id)
        paid = get_payments_by_invoice(invoice_id)
        due = float(inv["total_amount"]) - paid

        return success_response(
            result={
                "invoice": {
                    "id": inv["id"],
                    "invoice_number": inv["invoice_number"],
                    "created_at": inv["created_at"],
                    "due_date": inv["due_date"],
                    "status": inv["status"],
                    "tax_percent": inv["tax_percent"],
                    "discount_amount": inv["discount_amount"],
                    "total_amount": inv["total_amount"],
                    "paid_amount": paid,
                    "due_amount": due,
                },
                "customer": {
                    "id": inv["customer_id"],
                    "full_name": inv["customer_full_name"],
                    "email": inv["customer_email"],
                    "phone": inv["customer_phone"],
                    "address": inv["customer_address"],
                },
                "items": items,
            },
            message="Invoice details fetched successfully",
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@invoices_bp.put("/<invoice_id>")
@require_auth
def update(invoice_id):
    try:
        data = request.json or {}
        validated: Dict[str, Any] = update_schema.load(data)

        updated_invoice = update_invoice(invoice_id, **validated)
        if not updated_invoice:
            return error_response(
                type="not_found",
                message="Invoice does not exist",
                details=[],
                status=400,
            )

        return success_response(
            message="Invoice updated successfully",
            result=updated_invoice,
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@invoices_bp.post("/<invoice_id>/pay")
@require_auth
def pay(invoice_id):
    try:
        data: Dict[str, Any] = payment_schema.load(request.json or {})
        create_payment(
            invoice_id=invoice_id,
            amount=data["amount"],
            payment_date=data.get("payment_date", str(date.today())),
            method=data.get("method", "upi"),
            reference_number=data["reference_no"],
        )

        return success_response(
            message="Payment recorded successfully",
            result={
                "invoice_id": invoice_id,
                "amount": data["amount"],
                "method": data.get("method", "upi"),
                "payment_date": str(data.get("payment_date", date.today())),
                "reference_no": data.get("reference_no"),
            },
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )
    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@invoices_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    try:
        data = request.json or {}
        validated: Dict[str, Any] = bulk_delete_schema.load(data)

        deleted_count = bulk_delete_invoices(validated["ids"])
        return success_response(
            message="Invoices deleted successfully",
            result={"deleted_count": deleted_count},
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )
    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )

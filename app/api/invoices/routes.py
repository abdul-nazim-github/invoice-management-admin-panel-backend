# =============================
# app/api/invoices/routes.py
# =============================
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List
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
    mark_invoice_as_paid,
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

# Schemas
create_schema = InvoiceCreateSchema()
update_schema = InvoiceUpdateSchema()
bulk_delete_schema = InvoiceBulkDeleteSchema()
filter_schema = InvoiceFilterSchema()
payment_schema = PaymentCreateSchema()


# ------------------------------
# Add Invoice
# ------------------------------
@invoices_bp.post("/")
@require_auth
def add_invoice():
    conn = None
    try:
        conn = get_db_connection()
        data = request.json or {}
        validated: Dict[str, Any] = create_schema.load(data)
        items: List[Dict[str, Any]] = validated.get("items", [])

        # ---------- Calculate subtotal ----------
        subtotal_amount = Decimal("0.00")
        for it in items:
            prod = get_product(it["product_id"])
            if not prod:
                return error_response(
                    type="invalid_product",
                    message="Invalid product",
                    details={
                        "product_id": [f"Product {it['product_id']} does not exist"]
                    },
                    status=400,
                )
            subtotal_amount += Decimal(str(prod["unit_price"])) * Decimal(
                it.get("quantity", 1)
            )

        # ---------- Convert and calculate totals ----------
        tax_percent = Decimal(str(validated.get("tax_percent", "0")))
        discount_amount = Decimal(str(validated.get("discount_amount", "0")))
        amount_paid = Decimal(str(validated.get("amount_paid", "0")))

        tax_amount = (subtotal_amount * tax_percent / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_amount = (subtotal_amount + tax_amount - discount_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # ---------- Validate amount_paid ----------
        if amount_paid > total_amount:
            raise ValidationError(
                "Amount paid cannot be greater than the total invoice amount"
            )

        # ---------- Create invoice ----------
        try:
            invoice_id = create_invoice(
                conn,
                customer_id=str(validated["customer_id"]),
                due_date=validated["due_date"],
                tax_percent=tax_percent,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                subtotal_amount=subtotal_amount,
                total_amount=total_amount,
                amount_paid=amount_paid,
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
                int(it.get("quantity", 1)),
                Decimal(str(prod["unit_price"])),
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
        if conn:
            conn.close()


# ------------------------------
# List Invoices
# ------------------------------
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
            paid = Decimal(str(get_payments_by_invoice(inv["id"])))
            inv["paid_amount"] = paid
            inv["due_amount"] = (Decimal(str(inv["total_amount"])) - paid).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

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


# ------------------------------
# Invoice Detail
# ------------------------------
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
        paid = Decimal(str(get_payments_by_invoice(invoice_id)))
        due = (Decimal(str(inv["total_amount"])) - paid).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return success_response(
            result={
                "id": inv["id"],
                "invoice_number": inv["invoice_number"],
                "created_at": inv["created_at"],
                "due_date": inv["due_date"],
                "status": inv["status"],
                "tax_percent": Decimal(str(inv["tax_percent"])),
                "tax_amount": Decimal(str(inv["tax_amount"])),
                "discount_amount": Decimal(str(inv["discount_amount"])),
                "subtotal_amount": Decimal(str(inv["subtotal_amount"])),
                "total_amount": Decimal(str(inv["total_amount"])),
                "paid_amount": paid,
                "due_amount": due,
                "customer": {
                    "id": inv["customer_id"],
                    "full_name": inv["full_name"],
                    "email": inv["email"],
                    "phone": inv["phone"],
                    "address": inv["address"],
                    "gst_number": inv["gst_number"],
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


# ------------------------------
# Update Invoice
# ------------------------------
@invoices_bp.put("/<invoice_id>")
@require_auth
def update(invoice_id):
    try:
        data = request.json or {}
        validated: Dict[str, Any] = update_schema.load(data)
        print('validated.get("is_mark_as_paid"): ', validated.get("is_mark_as_paid"))
        if validated.get("is_mark_as_paid"):  # If true, call payment-only update
            updated_invoice = mark_invoice_as_paid(invoice_id, validated["amount_paid"])
        else:  # Normal update flow
            validated.pop("is_mark_as_paid", None)
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

# ------------------------------
# Record Payment
# ------------------------------
@invoices_bp.post("/<invoice_id>/pay")
@require_auth
def pay(invoice_id):
    try:
        data: Dict[str, Any] = payment_schema.load(request.json or {})
        create_payment(
            invoice_id=invoice_id,
            amount=Decimal(str(data["amount"])),
            payment_date=data.get("payment_date", str(date.today())),
            method=data.get("method", "upi"),
            reference_number=data["reference_no"],
        )

        return success_response(
            message="Payment recorded successfully",
            result={
                "invoice_id": invoice_id,
                "amount": Decimal(str(data["amount"])),
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


# ------------------------------
# Bulk Delete
# ------------------------------
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

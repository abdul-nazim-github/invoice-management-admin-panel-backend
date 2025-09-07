# =============================
# app/api/customers/routes.py
# =============================
import re
from typing import Dict
from flask import Blueprint, request
from marshmallow import ValidationError
from pymysql.err import IntegrityError

from app.api.customers.schemas import (
    CustomerBulkDeleteSchema,
    CustomerCreateSchema,
    CustomerFilterSchema,
    CustomerUpdateSchema,
)
from app.utils.auth import require_auth
from app.utils.pagination import get_pagination
from app.database.models.customer_model import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
    bulk_delete_customers,
    customer_aggregates,
)
from app.utils.response import error_response, success_response

customers_bp = Blueprint("customers", __name__)

# schemas
create_schema = CustomerCreateSchema()
update_schema = CustomerUpdateSchema()
bulk_delete_schema = CustomerBulkDeleteSchema()
filter_schema = CustomerFilterSchema()


@customers_bp.post("/")
@require_auth
def add_customer():
    try:
        data = request.json or {}
        validated: Dict[str, str] = create_schema.load(data)

        cid = create_customer(
            validated["name"],
            validated.get("email"),
            validated.get("phone"),
            validated.get("address"),
            validated.get("gst_number"),
            validated.get("status", "active"),
        )
        return success_response(
            result={"id": cid},
            message="Customer created successfully",
        )

    except ValidationError as ve:
        return error_response(
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except IntegrityError as ie:
        # Duplicate entry handling
        msg = str(ie)
        details = {}

        if "Duplicate entry" in msg:
            match = re.search(r"Duplicate entry '(.+)' for key '.*\.(.+)'", msg)
            if match:
                value, field = match.groups()
                details[field] = [f"Duplicate entry '{value}'"]
            else:
                details["error"] = [msg]

            return error_response(
                message="Duplicate entry", details=details, status=409
            )
        # fallback for other IntegrityErrors
        return error_response(
            message="Integrity error", details={"error": [msg]}, status=400
        )

    except Exception as e:
        return error_response(
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@customers_bp.get("/")
@require_auth
def list_():
    try:
        args = request.args or {}
        validated: Dict[str, str] = filter_schema.load(args)

        page, limit, offset = get_pagination()
        rows, total = list_customers(
            q=validated.get("q"),
            status=validated.get("status"),
            offset=offset,
            limit=limit,
        )
        return success_response(
            result=rows,
            message="Customers fetched successfully",
            meta={"page": page, "limit": limit, "total": total},
        )

    except ValidationError as ve:
        return error_response(
            message="Validation Error",
            details=ve.messages,
            status=400,
        )


@customers_bp.get("/<customer_id>")
@require_auth
def detail(customer_id):
    customer = get_customer(customer_id)
    if not customer:
        return error_response(message="Customer not found", status=400)

    agg = customer_aggregates(customer_id)
    return success_response(
        result={"customer": customer, **agg},
        message="Customer details fetched successfully",
    )


@customers_bp.put("/<int:customer_id>")
@require_auth
def update(customer_id):
    try:
        data = request.json or {}
        validated = update_schema.load(data)

        update_customer(customer_id, **validated)
        return success_response(
            message="Customer updated successfully",
            result={"id": customer_id},
        )

    except ValidationError as ve:
        return error_response(
            message="Validation Error",
            details=ve.messages,
            status=400,
        )


@customers_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    try:
        data = request.json or {}
        validated: Dict[str] = bulk_delete_schema.load(data)

        deleted = bulk_delete_customers(validated["ids"])
        return success_response(
            message="Customers deleted successfully",
            result={"deleted": deleted},
        )

    except ValidationError as ve:
        return error_response(
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

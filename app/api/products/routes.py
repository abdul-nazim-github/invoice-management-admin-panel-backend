# =============================
# app/api/products/routes.py
# =============================
import re
from typing import Dict
from flask import Blueprint, request
from marshmallow import ValidationError
from pymysql.err import IntegrityError

from app.api.products.schemas import (
    ProductBulkDeleteSchema,
    ProductCreateSchema,
    ProductFilterSchema,
    ProductUpdateSchema,
)
from app.utils.auth import require_auth
from app.utils.pagination import get_pagination
from app.database.models.product_model import (
    create_product,
    list_products,
    get_product,
    update_product,
    bulk_delete_products,
)
from app.utils.response import error_response, success_response

products_bp = Blueprint("products", __name__)

# Schemas
create_schema = ProductCreateSchema()
update_schema = ProductUpdateSchema()
bulk_delete_schema = ProductBulkDeleteSchema()
filter_schema = ProductFilterSchema()


@products_bp.post("/")
@require_auth
def add_product():
    try:
        data = request.json or {}
        validated: Dict[str, str] = create_schema.load(data)

        product = create_product(
            validated["sku"],
            validated["name"],
            validated.get("description"),
            validated["unit_price"],
            validated.get("stock_quantity", 0),
        )
        return success_response(
            result=product,
            message="Product created successfully",
        )
    

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except IntegrityError as ie:
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
                type="duplicate_entry",
                message="Duplicate entry",
                details=details,
                status=409,
            )

        return error_response(
            type="integrity_error",
            message="Integrity error",
            details={"error": [msg]},
            status=400,
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@products_bp.get("/")
@require_auth
def list_():
    try:
        args = request.args or {}
        validated: Dict[str, str] = filter_schema.load(args)

        page, limit, offset = get_pagination()
        rows, total = list_products(
            q=validated.get("q"),
            offset=offset,
            limit=limit,
        )
        return success_response(
            result=rows,
            message="Products fetched successfully",
            meta={"page": page, "limit": limit, "total": total},
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


@products_bp.get("/<product_id>")
@require_auth
def detail(product_id):
    try:
        product = get_product(product_id)
        if not product:
            return error_response(
                type="not_found",
                message="Product not found",
                status=404,
            )

        return success_response(
            result=product,
            message="Product details fetched successfully",
        )
    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@products_bp.put("/<product_id>")
@require_auth
def update(product_id):
    try:
        data = request.json or {}
        validated: Dict[str, str] = update_schema.load(data)

        updated_product = update_product(product_id, **validated)
        return success_response(
            result=updated_product,
            message="Product updated successfully",
        )

    except ValidationError as ve:
        return error_response(
            type="validation_error",
            message="Validation Error",
            details=ve.messages,
            status=400,
        )

    except IntegrityError as ie:
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
                type="duplicate_entry",
                message="Duplicate entry",
                details=details,
                status=409,
            )

        return error_response(
            type="integrity_error",
            message="Integrity error",
            details={"error": [msg]},
            status=400,
        )

    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )


@products_bp.post("/bulk-delete")
@require_auth
def bulk_delete():
    try:
        data = request.json or {}
        validated: Dict[str] = bulk_delete_schema.load(data)

        deleted = bulk_delete_products(validated["ids"])
        return success_response(
            message="Products deleted successfully",
            result={"deleted": deleted},
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

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.database.models.product import Product
from app.schemas.product_schema import ProductSchema
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

products_blueprint = Blueprint('products', __name__)

# Instantiate schemas
product_schema = ProductSchema()
product_update_schema = ProductSchema(partial=True)

@products_blueprint.route('/products/search', methods=['GET'])
@jwt_required()
def search_products():
    search_term = request.args.get('q')
    if not search_term:
        return error_response('validation_error', message="Search term 'q' is required.", status=400)

    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

    try:
        products = Product.search(search_term, include_deleted=include_deleted)
        serialized_products = product_schema.dump(products, many=True)
        return success_response(serialized_products, message="Products matching the search term retrieved successfully.")
    except Exception as e:
        return error_response('server_error', message="An error occurred during the search.", details=str(e), status=500)


@products_blueprint.route('/products', methods=['POST'])
@jwt_required()
@require_admin
def create_product():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        validated_data = product_schema.load(data)
    except ValidationError as err:
        return error_response('validation_error', 
                              message="The provided data is invalid.",
                              details=err.messages,
                              status=400)

    try:
        product_id = Product.create(validated_data)
        if product_id:
            product = Product.find_by_id(product_id)
            if product:
                return success_response(product_schema.dump(product), message="Product created successfully.", status=201)
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_product"], 
                              status=500)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    page, per_page = get_pagination()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        products, total = Product.find_with_pagination_and_count(page=page, per_page=per_page, include_deleted=include_deleted)
        serialized_products = product_schema.dump(products, many=True)
        return success_response({
            'products': serialized_products,
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Products retrieved successfully.")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        product = Product.find_by_id(product_id, include_deleted=include_deleted)
        if product:
            return success_response(product_schema.dump(product), message="Product retrieved successfully.")
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["product"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_product(product_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        validated_data = product_update_schema.load(data)
    except ValidationError as err:
        return error_response('validation_error', 
                              message="The provided data is invalid.",
                              details=err.messages,
                              status=400)

    try:
        if not Product.update(product_id, validated_data):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        updated_product = Product.find_by_id(product_id)
        return success_response(product_schema.dump(updated_product), message="Product updated successfully.")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/bulk-delete', methods=['POST'])
@jwt_required()
@require_admin
def bulk_delete_products():
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return error_response('validation_error', message="Invalid request. 'ids' must be a list of product IDs.", status=400)

    ids_to_delete = data['ids']
    if not ids_to_delete:
        return error_response('validation_error', message="The 'ids' list cannot be empty.", status=400)

    try:
        deleted_count = Product.bulk_soft_delete(ids_to_delete)
        if deleted_count > 0:
            return success_response(message=f"{deleted_count} product(s) soft-deleted successfully.")
        return error_response('not_found', message="No matching products found for the provided IDs.", status=404)
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["delete_product"], details=str(e), status=500)

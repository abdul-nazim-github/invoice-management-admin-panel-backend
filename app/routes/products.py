from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.database.models.product import Product
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['POST'])
@jwt_required()
@require_admin
def create_product():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    required_fields = ['product_code', 'name', 'description', 'price', 'stock']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["missing_fields"],
                              details=f"Missing: {', '.join(missing_fields)}",
                              status=400)

    try:
        product_id = Product.create(data)
        if product_id:
            product = Product.find_by_id(product_id)
            if product:
                return success_response(product.to_dict(), message="Product created successfully", status=201)
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
        return success_response({
            'products': [p.to_dict() for p in products],
            'total': total,
            'page': page,
            'per_page': per_page
        })
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
            return success_response(product.to_dict())
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
        if not Product.update(product_id, data):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        updated_product = Product.find_by_id(product_id)
        return success_response(updated_product.to_dict(), message="Product updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_product(product_id):
    try:
        if not Product.soft_delete(product_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        return success_response(message="Product soft-deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_product"], 
                              details=str(e), 
                              status=500)

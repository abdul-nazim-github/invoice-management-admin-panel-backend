from flask import Blueprint, request
from app.database.models.product import Product
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['POST'])
@require_admin
def create_product():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    required_fields = ['product_code', 'name', 'description', 'price', 'stock', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["missing_fields"],
                              details=f"Missing: {', '.join(missing_fields)}",
                              status=400)

    try:
        product_id = Product.create(data)
        product = Product.find_by_id(product_id)
        return success_response(product.to_dict(), message="Product created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products', methods=['GET'])
def get_products():
    page, per_page = get_pagination()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        products = Product.find_with_pagination(page=page, per_page=per_page, include_deleted=include_deleted)
        total_products = Product.count(include_deleted=include_deleted)
        return success_response({
            'products': [p.to_dict() for p in products],
            'total': total_products,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
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
@require_admin
def update_product(product_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Product.find_by_id(product_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        Product.update(product_id, data)
        updated_product = Product.find_by_id(product_id)
        return success_response(updated_product.to_dict(), message="Product updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
@require_admin
def delete_product(product_id):
    try:
        if not Product.find_by_id(product_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        Product.soft_delete(product_id)
        return success_response(message="Product soft-deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_product"], 
                              details=str(e), 
                              status=500)

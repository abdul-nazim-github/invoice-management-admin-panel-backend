from flask import Blueprint, request
from app.database.models.product import Product
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.cache import cache
from app.api.dashboard.routes import dashboard_stats, sales_performance

products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['POST'])
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
        product = Product.get_by_id(product_id)
        cache.delete_memoized(get_products)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        return success_response(product, message="Product created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products', methods=['GET'])
@cache.cached()
def get_products():
    try:
        products = Product.get_all()
        return success_response(products)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
@cache.cached()
def get_product(product_id):
    try:
        product = Product.get_by_id(product_id)
        if product:
            return success_response(product)
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["product"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Product.get_by_id(product_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        Product.update(product_id, data)
        cache.delete_memoized(get_product, product_id)
        cache.delete_memoized(get_products)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        updated_product = Product.get_by_id(product_id)
        return success_response(updated_product, message="Product updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_product"], 
                              details=str(e), 
                              status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        if not Product.get_by_id(product_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["product"], 
                                  status=404)

        Product.delete(product_id)
        cache.delete_memoized(get_product, product_id)
        cache.delete_memoized(get_products)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        return success_response(message="Product deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_product"], 
                              details=str(e), 
                              status=500)

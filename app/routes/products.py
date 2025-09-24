from flask import Blueprint, request
from app.database.models.product import Product
from app.utils.response import success_response, error_response

products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)
    
    # Basic validation
    required_fields = ['product_code', 'name', 'description', 'price', 'stock', 'status']
    if not all(field in data for field in required_fields):
        return error_response('validation_error', 'Missing required fields', status=400)

    try:
        product = Product.create(data)
        return success_response(product, message="Product created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 'Could not create product', details=str(e), status=500)

@products_blueprint.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.get_all()
        return success_response(products)
    except Exception as e:
        return error_response('server_error', 'Could not fetch products', details=str(e), status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.get_by_id(product_id)
        if product:
            return success_response(product)
        return error_response('not_found', 'Product not found', status=404)
    except Exception as e:
        return error_response('server_error', 'Could not fetch product', details=str(e), status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    try:
        if not Product.get_by_id(product_id):
            return error_response('not_found', 'Product not found', status=404)

        product = Product.update(product_id, data)
        return success_response(product, message="Product updated successfully")
    except Exception as e:
        return error_response('server_error', 'Could not update product', details=str(e), status=500)

@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        if not Product.get_by_id(product_id):
            return error_response('not_found', 'Product not found', status=404)

        result = Product.delete(product_id)
        return success_response(result, message="Product deleted successfully")
    except Exception as e:
        return error_response('server_error', 'Could not delete product', details=str(e), status=500)

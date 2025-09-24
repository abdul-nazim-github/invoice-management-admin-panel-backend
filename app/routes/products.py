from flask import Blueprint, request, jsonify
from app.database.models.product import Product

products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    product = Product.create(data)
    return jsonify(product), 201

@products_blueprint.route('/products', methods=['GET'])
def get_products():
    products = Product.get_all()
    return jsonify(products)

@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.get_by_id(product_id)
    if product:
        return jsonify(product)
    return jsonify({'message': 'Product not found'}), 404

@products_blueprint.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    product = Product.update(product_id, data)
    if product:
        return jsonify(product)
    return jsonify({'message': 'Product not found'}), 404

@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if Product.delete(product_id):
        return jsonify({'message': 'Product deleted'})
    return jsonify({'message': 'Product not found'}), 404

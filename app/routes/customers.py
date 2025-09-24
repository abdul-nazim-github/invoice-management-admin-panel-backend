from flask import Blueprint, request, jsonify
from app.database.models.customer import Customer

customers_blueprint = Blueprint('customers', __name__)

@customers_blueprint.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    customer = Customer.create(data)
    return jsonify(customer), 201

@customers_blueprint.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.get_all()
    return jsonify(customers)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.get_by_id(customer_id)
    if customer:
        return jsonify(customer)
    return jsonify({'message': 'Customer not found'}), 404

@customers_blueprint.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    customer = Customer.update(customer_id, data)
    if customer:
        return jsonify(customer)
    return jsonify({'message': 'Customer not found'}), 404

@customers_blueprint.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    if Customer.delete(customer_id):
        return jsonify({'message': 'Customer deleted'})
    return jsonify({'message': 'Customer not found'}), 404

from flask import Blueprint, request
from app.database.models.customer import Customer
from app.utils.response import success_response, error_response

customers_blueprint = Blueprint('customers', __name__)

@customers_blueprint.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)
    
    # Basic validation
    required_fields = ['name', 'email', 'phone', 'address', 'gst_number', 'status']
    if not all(field in data for field in required_fields):
        return error_response('validation_error', 'Missing required fields', status=400)

    try:
        customer = Customer.create(data)
        return success_response(customer, message="Customer created successfully", status=201)
    except Exception as e:
        # In a real app, you would log this error
        return error_response('server_error', 'Could not create customer', details=str(e), status=500)

@customers_blueprint.route('/customers', methods=['GET'])
def get_customers():
    try:
        customers = Customer.get_all()
        return success_response(customers)
    except Exception as e:
        return error_response('server_error', 'Could not fetch customers', details=str(e), status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customer = Customer.get_by_id(customer_id)
        if customer:
            return success_response(customer)
        return error_response('not_found', 'Customer not found', status=404)
    except Exception as e:
        return error_response('server_error', 'Could not fetch customer', details=str(e), status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    try:
        # Check if the customer exists first
        if not Customer.get_by_id(customer_id):
            return error_response('not_found', 'Customer not found', status=404)

        customer = Customer.update(customer_id, data)
        return success_response(customer, message="Customer updated successfully")
    except Exception as e:
        return error_response('server_error', 'Could not update customer', details=str(e), status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        # Check if the customer exists first
        if not Customer.get_by_id(customer_id):
            return error_response('not_found', 'Customer not found', status=404)

        result = Customer.delete(customer_id)
        return success_response(result, message="Customer deleted successfully")
    except Exception as e:
        return error_response('server_error', 'Could not delete customer', details=str(e), status=500)

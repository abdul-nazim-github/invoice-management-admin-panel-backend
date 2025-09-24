from flask import Blueprint, request
from app.database.models.customer import Customer
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES

customers_blueprint = Blueprint('customers', __name__)

@customers_blueprint.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    required_fields = ['name', 'email', 'phone', 'address', 'gst_number', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["missing_fields"],
                              details=f"Missing: {', '.join(missing_fields)}",
                              status=400)

    try:
        customer_id = Customer.create(data)
        customer = Customer.get_by_id(customer_id)
        return success_response(customer, message="Customer created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers', methods=['GET'])
def get_customers():
    try:
        customers = Customer.get_all()
        return success_response(customers)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customer = Customer.get_by_id(customer_id)
        if customer:
            return success_response(customer)
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["customer"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Customer.get_by_id(customer_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["customer"], 
                                  status=404)

        Customer.update(customer_id, data)
        updated_customer = Customer.get_by_id(customer_id)
        return success_response(updated_customer, message="Customer updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        if not Customer.get_by_id(customer_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["customer"], 
                                  status=404)

        Customer.delete(customer_id)
        return success_response(message="Customer deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_customer"], 
                              details=str(e), 
                              status=500)

from flask import Blueprint, request
from app.database.models.customer import Customer
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

customers_blueprint = Blueprint('customers', __name__)

@customers_blueprint.route('/customers', methods=['POST'])
@require_admin
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
        customer = Customer.find_by_id(customer_id)
        return success_response(customer.to_dict(), message="Customer created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers', methods=['GET'])
def get_customers():
    page, per_page = get_pagination()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        customers = Customer.find_with_pagination(page=page, per_page=per_page, include_deleted=include_deleted)
        total_customers = Customer.count(include_deleted=include_deleted)
        return success_response({
            'customers': [c.to_dict() for c in customers],
            'total': total_customers,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        customer = Customer.find_by_id(customer_id, include_deleted=include_deleted)
        if customer:
            return success_response(customer.to_dict())
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["customer"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['PUT'])
@require_admin
def update_customer(customer_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Customer.find_by_id(customer_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["customer"], 
                                  status=404)

        Customer.update(customer_id, data)
        updated_customer = Customer.find_by_id(customer_id)
        return success_response(updated_customer.to_dict(), message="Customer updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['DELETE'])
@require_admin
def delete_customer(customer_id):
    try:
        if not Customer.find_by_id(customer_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["customer"], 
                                  status=404)

        Customer.soft_delete(customer_id)
        return success_response(message="Customer soft-deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_customer"], 
                              details=str(e), 
                              status=500)

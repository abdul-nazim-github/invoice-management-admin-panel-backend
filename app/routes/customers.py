from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.database.models.customer import Customer
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination
from app.utils.validation import validate_customer_data

customers_blueprint = Blueprint('customers', __name__)

@customers_blueprint.route('/customers', methods=['POST'])
@jwt_required()
@require_admin
def create_customer():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    # Validate incoming data
    validation_errors = validate_customer_data(data)
    if validation_errors:
        return error_response('validation_error', 
                              message="The provided data is invalid.",
                              details=validation_errors,
                              status=400)

    # Check for existing customer with the same email
    if 'email' in data and data['email']:
        existing_customer = Customer.find_by_email(data['email'])
        if existing_customer:
            return error_response('conflict', message='A customer with this email address already exists.', status=409)

    try:
        customer_id = Customer.create(data)
        if customer_id:
            # Fetch the customer with payment status to return a consistent response
            customer = Customer.find_by_id(customer_id)
            if customer:
                return success_response(customer.to_dict(), message="Customer created successfully.", status=201)
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              status=500)
    except Exception as e:
        # Check for unique constraint violation from the database
        if 'UNIQUE constraint failed: customers.email' in str(e) or 'Duplicate entry' in str(e):
             return error_response('conflict', message='A customer with this email address already exists.', status=409)
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    page, per_page = get_pagination()
    q = request.args.get('q', None)
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    
    try:
        customers, total = Customer.list_all(
            q=q, 
            offset=(page - 1) * per_page, 
            limit=per_page, 
            include_deleted=include_deleted
        )
        return success_response({
            'customers': [c.to_dict() for c in customers],
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Customers retrieved successfully.")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        # This now returns a single customer with their payment status
        customer = Customer.find_by_id(customer_id, include_deleted=include_deleted)
        if customer:
            return success_response(customer.to_dict(), message="Customer retrieved successfully.")
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["customer"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_customer(customer_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    # Validate incoming data
    validation_errors = validate_customer_data(data, is_update=True)
    if validation_errors:
        return error_response('validation_error', 
                              message="The provided data is invalid.",
                              details=validation_errors,
                              status=400)

    try:
        if not Customer.update(customer_id, data):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["customer"], 
                                  status=404)

        updated_customer = Customer.find_by_id(customer_id)
        return success_response(updated_customer.to_dict(), message="Customer updated successfully.")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_customer"], 
                              details=str(e), 
                              status=500)


@customers_blueprint.route('/customers/bulk-delete', methods=['POST'])
@jwt_required()
@require_admin
def bulk_delete_customers():
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return error_response('validation_error', 
                              message="Invalid request. 'ids' must be a list of customer IDs.",
                              status=400)

    ids_to_delete = data['ids']
    if not ids_to_delete:
        return error_response('validation_error', 
                              message="The 'ids' list cannot be empty.",
                              status=400)

    try:
        deleted_count = Customer.bulk_soft_delete(ids_to_delete)
        if deleted_count > 0:
            return success_response(message=f"{deleted_count} customer(s) soft-deleted successfully.")
        return error_response('not_found', 
                              message="No matching customers found for the provided IDs.", 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_customer"], 
                              details=str(e), 
                              status=500)

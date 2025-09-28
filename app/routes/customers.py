from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.database.models.customer import Customer
from app.schemas.customer_schema import CustomerSchema, CustomerSummarySchema, CustomerDetailSchema, CustomerUpdateSchema
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

customers_blueprint = Blueprint('customers', __name__)

# Instantiate schemas
customer_schema = CustomerSchema()
customer_summary_schema = CustomerSummarySchema()
customer_detail_schema = CustomerDetailSchema()
customer_update_schema = CustomerUpdateSchema()

@customers_blueprint.route('/customers', methods=['POST'])
@jwt_required()
@require_admin
def create_customer():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        validated_data = customer_schema.load(data)
    except ValidationError as err:
        return error_response(
            'validation_error',
            message="The provided data is invalid.",
            details=err.messages,
            status=400
        )

    if 'email' in validated_data and validated_data['email']:
        existing_customer = Customer.find_by_email(validated_data['email'], include_deleted=True)
        if existing_customer:
            if existing_customer.deleted_at is None:
                return error_response('conflict', message='A customer with this email address already exists.', status=409)
            else:
                return error_response(
                    'conflict',
                    message='A soft-deleted customer with this email address already exists. Please use a different email.',
                    status=409
                )

    try:
        customer_id = Customer.create(validated_data)
        if customer_id:
            customer = Customer.find_by_id_with_aggregates(customer_id)
            if customer:
                return success_response(customer_summary_schema.dump(customer), message="Customer created successfully.", status=201)
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              status=500)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    page, per_page = get_pagination()
    q = request.args.get('q', None)
    status = request.args.get('status', None)
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    
    try:
        customers, total = Customer.list_all(
            q=q, 
            status=status,
            offset=(page - 1) * per_page, 
            limit=per_page, 
            include_deleted=include_deleted
        )
        serialized_customers = customer_summary_schema.dump(customers, many=True)
        return success_response({
            'customers': serialized_customers,
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Customers retrieved successfully.")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<string:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        customer = Customer.find_by_id_with_aggregates(customer_id, include_deleted=include_deleted)
        if customer:
            return success_response(customer_detail_schema.dump(customer), message="Customer details fetched successfully")
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["customer"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_customer"], 
                              details=str(e), 
                              status=500)

@customers_blueprint.route('/customers/<string:customer_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_customer(customer_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        validated_data = customer_update_schema.load(data)
    except ValidationError as err:
        return error_response(
            'validation_error',
            message="The provided data is invalid.",
            details=err.messages,
            status=400
        )

    try:
        # First, ensure the customer exists.
        customer_to_update = Customer.find_by_id(customer_id)
        if not customer_to_update:
            return error_response('not_found', message=ERROR_MESSAGES["not_found"]["customer"], status=404)

        # If email is being updated, check for conflicts.
        if 'email' in validated_data and validated_data['email']:
            existing_customer = Customer.find_by_email(validated_data['email'], include_deleted=True)
            if existing_customer and str(existing_customer.id) != str(customer_id):
                return error_response(
                    'conflict',
                    message='A customer with this email address already exists (active or deleted).'
                )

        # Proceed with the update.
        Customer.update(customer_id, validated_data)

        # Fetch the updated data and return it.
        updated_customer = Customer.find_by_id_with_aggregates(customer_id)
        return success_response(customer_summary_schema.dump(updated_customer), message="Customer updated successfully.")

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

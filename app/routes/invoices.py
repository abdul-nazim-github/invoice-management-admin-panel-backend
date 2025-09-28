from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.database.models.invoice import Invoice
from app.database.models.product import Product
from app.schemas.invoice_schema import InvoiceSchema
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

invoices_blueprint = Blueprint('invoices', __name__)

# Instantiate schemas
invoice_schema = InvoiceSchema()
invoice_update_schema = InvoiceSchema(partial=True)

@invoices_blueprint.route('/invoices/search', methods=['GET'])
@jwt_required()
def search_invoices():
    search_term = request.args.get('q')
    if not search_term:
        return error_response('validation_error', message="Search term 'q' is required.", status=400)

    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

    try:
        invoices = Invoice.search(search_term, include_deleted=include_deleted)
        serialized_invoices = invoice_schema.dump(invoices, many=True)
        return success_response(serialized_invoices, message="Invoices matching the search term retrieved successfully.")
    except Exception as e:
        return error_response('server_error', message="An error occurred during the search.", details=str(e), status=500)


@invoices_blueprint.route('/invoices', methods=['POST'])
@jwt_required()
@require_admin
def create_invoice():
    data = request.get_json()
    if not data:
        return error_response('validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        # Validate and deserialize the request data
        validated_data = invoice_schema.load(data)
    except ValidationError as err:
        return error_response(
            'validation_error',
            message="The provided data is invalid.",
            details=err.messages,
            status=400
        )

    try:
        # Calculate total_amount from product prices
        total_amount = 0
        for item in validated_data['items']:
            product = Product.find_by_id(item['product_id'])
            if not product:
                return error_response('not_found', message=f"Product with ID {item['product_id']} not found.", status=404)
            total_amount += product.price * item['quantity']

        invoice_data = {
            'customer_id': validated_data['customer_id'],
            'due_date': validated_data['due_date'],
            'total_amount': total_amount,
            'status': validated_data.get('status', 'pending')
        }

        invoice_id = Invoice.create(invoice_data)
        if not invoice_id:
            return error_response('server_error', message="Failed to create the invoice record.", status=500)

        for item in validated_data['items']:
            Invoice.add_item(invoice_id, item['product_id'], item['quantity'])

        new_invoice = Invoice.find_by_id(invoice_id)
        if new_invoice:
            return success_response(invoice_schema.dump(new_invoice), message="Invoice created successfully.", status=201)
        else:
            return error_response('not_found', message="Newly created invoice could not be found.", status=404)
            
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["create_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    page, per_page = get_pagination()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        invoices, total = Invoice.find_with_pagination_and_count(page=page, per_page=per_page, include_deleted=include_deleted)
        serialized_invoices = invoice_schema.dump(invoices, many=True)
        return success_response({
            'invoices': serialized_invoices,
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Invoices retrieved successfully.")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        invoice = Invoice.find_by_id(invoice_id, include_deleted=include_deleted)
        if invoice:
            return success_response(invoice_schema.dump(invoice), message="Invoice retrieved successfully.")
        return error_response('not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_invoice(invoice_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        validated_data = invoice_update_schema.load(data)
    except ValidationError as err:
        return error_response('validation_error', message="The provided data is invalid.", details=err.messages, status=400)

    try:
        if not Invoice.update(invoice_id, validated_data):
            return error_response('not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

        updated_invoice = Invoice.find_by_id(invoice_id)
        return success_response(invoice_schema.dump(updated_invoice), message="Invoice updated successfully.")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["update_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/bulk-delete', methods=['POST'])
@jwt_required()
@require_admin
def bulk_delete_invoices():
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return error_response('validation_error', message="Invalid request. 'ids' must be a list of invoice IDs.", status=400)

    ids_to_delete = data['ids']
    if not ids_to_delete:
        return error_response('validation_error', message="The 'ids' list cannot be empty.", status=400)

    try:
        deleted_count = Invoice.bulk_soft_delete(ids_to_delete)
        if deleted_count > 0:
            return success_response(message=f"{deleted_count} invoice(s) soft-deleted successfully.")
        return error_response('not_found', message="No matching invoices found for the provided IDs.", status=404)
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["delete_invoice"], details=str(e), status=500)

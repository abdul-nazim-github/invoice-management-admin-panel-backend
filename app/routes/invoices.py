from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from decimal import Decimal, ROUND_HALF_UP

from app.database.models.invoice import Invoice
from app.database.models.product import Product
from app.schemas.invoice_schema import InvoiceSchema
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

invoices_blueprint = Blueprint('invoices', __name__)

invoice_schema = InvoiceSchema()
invoice_update_schema = InvoiceSchema(partial=True)

@invoices_blueprint.route('/invoices', methods=['POST'])
@jwt_required()
@require_admin
def create_invoice():
    data = request.get_json()
    if not data:
        return error_response(error_code='validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        validated_data = invoice_schema.load(data)
    except ValidationError as err:
        return error_response(error_code='validation_error', message="The provided data is invalid.", details=err.messages, status=400)

    try:
        current_user_id = get_jwt_identity()
        
        # Use Decimal for all financial calculations
        subtotal_amount = Decimal('0.00')
        for item in validated_data['items']:
            product = Product.find_by_id(item['product_id'])
            if not product:
                return error_response(error_code='not_found', message=f"Product with ID {item['product_id']} not found.", status=404)
            # Ensure product.price is a Decimal
            subtotal_amount += Decimal(product.price) * Decimal(item['quantity'])

        # Get Decimal values from validated data, providing default
        tax_percent = Decimal(validated_data.get('tax_percent', '0.00'))
        discount_amount = Decimal(validated_data.get('discount_amount', '0.00'))

        # Perform calculations with Decimal
        taxable_amount = subtotal_amount - discount_amount
        tax_amount = (taxable_amount * (tax_percent / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount = taxable_amount + tax_amount

        invoice_data = {
            'customer_id': validated_data['customer_id'],
            'user_id': current_user_id,
            'due_date': validated_data['due_date'],
            'subtotal_amount': subtotal_amount,
            'discount_amount': discount_amount,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': validated_data.get('status', 'Pending')
        }

        # The Invoice model will handle quantization before DB insertion
        invoice_id = Invoice.create(invoice_data)
        if not invoice_id:
            return error_response(error_code='server_error', message="Failed to create the invoice record.", status=500)

        for item in validated_data['items']:
            Invoice.add_item(invoice_id, item['product_id'], item['quantity'])

        new_invoice = Invoice.find_by_id(invoice_id)
        # Use the schema to dump the data for a consistent response format
        return success_response(invoice_schema.dump(new_invoice), message="Invoice created successfully.", status=201)
            
    except Exception as e:
        return error_response(error_code='server_error', message=ERROR_MESSAGES["server_error"]["create_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    page, per_page = get_pagination()
    q = request.args.get('q')
    status = request.args.get('status')
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

    try:
        invoices, total = Invoice.list_all(q=q, status=status, offset=(page - 1) * per_page, limit=per_page, include_deleted=include_deleted)
        
        # Use the schema for serialization to ensure consistency
        serialized_invoices = invoice_schema.dump(invoices, many=True)

        return success_response({
            'invoices': serialized_invoices,
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Invoices retrieved successfully.")
    except Exception as e:
        return error_response(error_code='server_error', message=ERROR_MESSAGES["server_error"]["fetch_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        invoice = Invoice.find_by_id(invoice_id, include_deleted=include_deleted)
        if invoice:
            # Use the schema for serialization
            return success_response(invoice_schema.dump(invoice), message="Invoice retrieved successfully.")
        return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)
    except Exception as e:
        return error_response(error_code='server_error', message=ERROR_MESSAGES["server_error"]["fetch_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_invoice(invoice_id):
    data = request.get_json()
    if not data:
        return error_response(error_code='validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        validated_data = invoice_update_schema.load(data)
    except ValidationError as err:
        return error_response(error_code='validation_error', message="The provided data is invalid.", details=err.messages, status=400)

    try:
        # The update logic will also need to be updated to handle Decimal correctly
        # For now, this just updates based on validated data
        if not Invoice.update(invoice_id, validated_data):
            return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

        updated_invoice = Invoice.find_by_id(invoice_id)
        return success_response(invoice_schema.dump(updated_invoice), message="Invoice updated successfully.")
    except Exception as e:
        return error_response(error_code='server_error', message=ERROR_MESSAGES["server_error"]["update_invoice"], details=str(e), status=500)

@invoices_blueprint.route('/invoices/bulk-delete', methods=['POST'])
@jwt_required()
@require_admin
def bulk_delete_invoices():
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return error_response(error_code='validation_error', message="Invalid request. 'ids' must be a list of invoice IDs.", status=400)

    ids_to_delete = data['ids']
    if not ids_to_delete:
        return error_response(error_code='validation_error', message="The 'ids' list cannot be empty.", status=400)

    try:
        deleted_count = Invoice.bulk_soft_delete(ids_to_delete)
        if deleted_count > 0:
            return success_response(message=f"{deleted_count} invoice(s) soft-deleted successfully.")
        return error_response(error_code='not_found', message="No matching invoices found for the provided IDs.", status=404)
    except Exception as e:
        return error_response(error_code='server_error', message=ERROR_MESSAGES["server_error"]["delete_invoice"], details=str(e), status=500)

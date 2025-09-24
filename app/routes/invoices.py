from flask import Blueprint, request
from app.database.models.invoice import Invoice
from app.utils.response import success_response, error_response

invoices_blueprint = Blueprint('invoices', __name__)

@invoices_blueprint.route('/invoices', methods=['POST'])
def create_invoice():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    required_fields = ['customer_id', 'invoice_date', 'total_amount', 'status']
    if not all(field in data for field in required_fields):
        return error_response('validation_error', 'Missing required fields', status=400)

    try:
        invoice = Invoice.create(data)
        return success_response(invoice, message="Invoice created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 'Could not create invoice', details=str(e), status=500)

@invoices_blueprint.route('/invoices', methods=['GET'])
def get_invoices():
    try:
        invoices = Invoice.get_all()
        return success_response(invoices)
    except Exception as e:
        return error_response('server_error', 'Could not fetch invoices', details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    try:
        invoice = Invoice.get_by_id(invoice_id)
        if invoice:
            return success_response(invoice)
        return error_response('not_found', 'Invoice not found', status=404)
    except Exception as e:
        return error_response('server_error', 'Could not fetch invoice', details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    try:
        if not Invoice.get_by_id(invoice_id):
            return error_response('not_found', 'Invoice not found', status=404)

        invoice = Invoice.update(invoice_id, data)
        return success_response(invoice, message="Invoice updated successfully")
    except Exception as e:
        return error_response('server_error', 'Could not update invoice', details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        if not Invoice.get_by_id(invoice_id):
            return error_response('not_found', 'Invoice not found', status=404)

        result = Invoice.delete(invoice_id)
        return success_response(result, message="Invoice deleted successfully")
    except Exception as e:
        return error_response('server_error', 'Could not delete invoice', details=str(e), status=500)

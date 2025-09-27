from flask import Blueprint, request
from app.database.models.invoice import Invoice
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES

invoices_blueprint = Blueprint('invoices', __name__)

@invoices_blueprint.route('/invoices', methods=['POST'])
def create_invoice():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    required_fields = ['customer_id', 'invoice_date', 'total_amount', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["missing_fields"],
                              details=f"Missing: {', '.join(missing_fields)}",
                              status=400)

    try:
        invoice_id = Invoice.create(data)
        invoice = Invoice.find_by_id(invoice_id)
        return success_response(invoice.to_dict(), message="Invoice created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_invoice"], 
                              details=str(e), 
                              status=500)

@invoices_blueprint.route('/invoices', methods=['GET'])
def get_invoices():
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        invoices = Invoice.find_all(include_deleted=include_deleted)
        return success_response([i.to_dict() for i in invoices])
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_invoice"], 
                              details=str(e), 
                              status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        invoice = Invoice.find_by_id(invoice_id, include_deleted=include_deleted)
        if invoice:
            return success_response(invoice.to_dict())
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["invoice"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_invoice"], 
                              details=str(e), 
                              status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Invoice.find_by_id(invoice_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["invoice"], 
                                  status=404)

        Invoice.update(invoice_id, data)
        updated_invoice = Invoice.find_by_id(invoice_id)
        return success_response(updated_invoice.to_dict(), message="Invoice updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_invoice"], 
                              details=str(e), 
                              status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        if not Invoice.find_by_id(invoice_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["invoice"], 
                                  status=404)

        Invoice.soft_delete(invoice_id)
        return success_response(message="Invoice soft-deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_invoice"], 
                              details=str(e), 
                              status=500)

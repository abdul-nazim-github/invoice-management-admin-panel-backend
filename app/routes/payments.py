from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.database.models.invoice import Invoice
from app.database.models.payment import Payment
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination
from app.utils.validation import validate_payment_data

payments_blueprint = Blueprint('payments', __name__)

@payments_blueprint.route('/payments/search', methods=['GET'])
@jwt_required()
def search_payments():
    search_term = request.args.get('q')
    if not search_term:
        return error_response('validation_error', message="Search term 'q' is required.", status=400)

    try:
        payments = Payment.search(search_term)
        return success_response([p.to_dict() for p in payments], message="Payments matching the search term retrieved successfully.")
    except Exception as e:
        return error_response('server_error', message="An error occurred during the search.", details=str(e), status=500)


@payments_blueprint.route('/payments', methods=['POST'])
@jwt_required()
@require_admin
def create_payment():
    data = request.get_json()
    if not data:
        return error_response('validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    validation_errors = validate_payment_data(data)
    if validation_errors:
        return error_response('validation_error', message="The provided payment data is invalid.", details=validation_errors, status=400)

    try:
        invoice = Invoice.find_by_id(data['invoice_id'])
        if not invoice:
            return error_response('not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

        payment_id = Payment.create(data)

        if payment_id:
            # Fetch the new payment to return its full details
            new_payment = Payment.find_by_id(payment_id)
            return success_response(new_payment.to_dict(), message="Payment recorded successfully.", status=201)
        return error_response('server_error', message="Failed to record payment.", status=500)
    except Exception as e:
        return error_response('server_error', message="An error occurred while recording the payment.", details=str(e), status=500)


@payments_blueprint.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    page, per_page = get_pagination()
    try:
        payments, total = Payment.find_with_pagination_and_count(page=page, per_page=per_page)
        return success_response({
            'payments': [p.to_dict() for p in payments],
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Payments retrieved successfully.")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_payment"], details=str(e), status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    try:
        payment = Payment.find_by_id(payment_id)
        if payment:
            return success_response(payment.to_dict(), message="Payment retrieved successfully.")
        return error_response('not_found', message=ERROR_MESSAGES["not_found"]["payment"], status=404)
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_payment"], details=str(e), status=500)

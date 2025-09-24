from flask import Blueprint, request
from app.database.models.payment import Payment
from app.utils.response import success_response, error_response

payments_blueprint = Blueprint('payments', __name__)

@payments_blueprint.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    required_fields = ['invoice_id', 'payment_date', 'amount', 'payment_method', 'status']
    if not all(field in data for field in required_fields):
        return error_response('validation_error', 'Missing required fields', status=400)

    try:
        payment = Payment.create(data)
        return success_response(payment, message="Payment created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 'Could not create payment', details=str(e), status=500)

@payments_blueprint.route('/payments', methods=['GET'])
def get_payments():
    try:
        payments = Payment.get_all()
        return success_response(payments)
    except Exception as e:
        return error_response('server_error', 'Could not fetch payments', details=str(e), status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        payment = Payment.get_by_id(payment_id)
        if payment:
            return success_response(payment)
        return error_response('not_found', 'Payment not found', status=404)
    except Exception as e:
        return error_response('server_error', 'Could not fetch payment', details=str(e), status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 'Request body cannot be empty', status=400)

    try:
        if not Payment.get_by_id(payment_id):
            return error_response('not_found', 'Payment not found', status=404)

        payment = Payment.update(payment_id, data)
        return success_response(payment, message="Payment updated successfully")
    except Exception as e:
        return error_response('server_error', 'Could not update payment', details=str(e), status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    try:
        if not Payment.get_by_id(payment_id):
            return error_response('not_found', 'Payment not found', status=404)

        result = Payment.delete(payment_id)
        return success_response(result, message="Payment deleted successfully")
    except Exception as e:
        return error_response('server_error', 'Could not delete payment', details=str(e), status=500)

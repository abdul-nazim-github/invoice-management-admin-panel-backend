from flask import Blueprint, request
from app.database.models.payment import Payment
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.cache import cache
from app.api.dashboard.routes import dashboard_stats, sales_performance

payments_blueprint = Blueprint('payments', __name__)

@payments_blueprint.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    required_fields = ['invoice_id', 'payment_date', 'amount', 'payment_method', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["missing_fields"],
                              details=f"Missing: {', '.join(missing_fields)}",
                              status=400)

    try:
        payment_id = Payment.create(data)
        payment = Payment.get_by_id(payment_id)
        cache.delete_memoized(get_payments)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        return success_response(payment, message="Payment created successfully", status=201)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["create_payment"], 
                              details=str(e), 
                              status=500)

@payments_blueprint.route('/payments', methods=['GET'])
@cache.cached()
def get_payments():
    try:
        payments = Payment.get_all()
        return success_response(payments)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_payment"], 
                              details=str(e), 
                              status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['GET'])
@cache.cached()
def get_payment(payment_id):
    try:
        payment = Payment.get_by_id(payment_id)
        if payment:
            return success_response(payment)
        return error_response('not_found', 
                              message=ERROR_MESSAGES["not_found"]["payment"], 
                              status=404)
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["fetch_payment"], 
                              details=str(e), 
                              status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    data = request.get_json()
    if not data:
        return error_response('validation_error', 
                              message=ERROR_MESSAGES["validation"]["request_body_empty"], 
                              status=400)

    try:
        if not Payment.get_by_id(payment_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["payment"], 
                                  status=404)

        Payment.update(payment_id, data)
        cache.delete_memoized(get_payment, payment_id)
        cache.delete_memoized(get_payments)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        updated_payment = Payment.get_by_id(payment_id)
        return success_response(updated_payment, message="Payment updated successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["update_payment"], 
                              details=str(e), 
                              status=500)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    try:
        if not Payment.get_by_id(payment_id):
            return error_response('not_found', 
                                  message=ERROR_MESSAGES["not_found"]["payment"], 
                                  status=404)

        Payment.delete(payment_id)
        cache.delete_memoized(get_payment, payment_id)
        cache.delete_memoized(get_payments)
        cache.delete_memoized(dashboard_stats)
        cache.delete_memoized(sales_performance)
        return success_response(message="Payment deleted successfully")
    except Exception as e:
        return error_response('server_error', 
                              message=ERROR_MESSAGES["server_error"]["delete_payment"], 
                              details=str(e), 
                              status=500)

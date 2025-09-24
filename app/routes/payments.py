from flask import Blueprint, request, jsonify
from app.database.models.payment import Payment

payments_blueprint = Blueprint('payments', __name__)

@payments_blueprint.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    payment = Payment.create(data)
    return jsonify(payment), 201

@payments_blueprint.route('/payments', methods=['GET'])
def get_payments():
    payments = Payment.get_all()
    return jsonify(payments)

@payments_blueprint.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.get_by_id(payment_id)
    if payment:
        return jsonify(payment)
    return jsonify({'message': 'Payment not found'}), 404

@payments_blueprint.route('/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    data = request.get_json()
    payment = Payment.update(payment_id, data)
    if payment:
        return jsonify(payment)
    return jsonify({'message': 'Payment not found'}), 404

@payments_blueprint.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    if Payment.delete(payment_id):
        return jsonify({'message': 'Payment deleted'})
    return jsonify({'message': 'Payment not found'}), 404

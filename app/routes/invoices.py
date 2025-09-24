from flask import Blueprint, request, jsonify
from app.database.models.invoice import Invoice

invoices_blueprint = Blueprint('invoices', __name__)

@invoices_blueprint.route('/invoices', methods=['POST'])
def create_invoice():
    data = request.get_json()
    invoice = Invoice.create(data)
    return jsonify(invoice), 201

@invoices_blueprint.route('/invoices', methods=['GET'])
def get_invoices():
    invoices = Invoice.get_all()
    return jsonify(invoices)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.get_by_id(invoice_id)
    if invoice:
        return jsonify(invoice)
    return jsonify({'message': 'Invoice not found'}), 404

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    data = request.get_json()
    invoice = Invoice.update(invoice_id, data)
    if invoice:
        return jsonify(invoice)
    return jsonify({'message': 'Invoice not found'}), 404

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    if Invoice.delete(invoice_id):
        return jsonify({'message': 'Invoice deleted'})
    return jsonify({'message': 'Invoice not found'}), 404

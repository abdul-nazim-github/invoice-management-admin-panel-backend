from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.invoice_schema import invoice_schema
from app.utils.error_messages import ERROR_MESSAGES
from app.database.models.invoice import Invoice
from app.database.models.product import Product
from app.database.models.customer import Customer # Import Customer model
from app.database.models.payment import Payment
from decimal import Decimal
from datetime import datetime
from app.utils.auth import require_admin
from app.utils.response import success_response, error_response

# Create a Blueprint for invoices
invoices_blueprint = Blueprint('invoices', __name__)

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
        # --- START: Customer and Product Validation ---
        customer = Customer.find_by_id(validated_data['customer_id'])
        if not customer:
            return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["customer"], status=404)

        subtotal_amount = Decimal('0.00')
        for item in validated_data['items']:
            product = Product.find_by_id(item['product_id'])
            if not product:
                return error_response(error_code='not_found', message=f"Product with ID {item['product_id']} not found.", status=404)
            subtotal_amount += Decimal(product.price) * Decimal(item['quantity'])
        # --- END: Customer and Product Validation ---

        current_user_id = get_jwt_identity()
        discount_amount = validated_data.get('discount_amount', Decimal('0.00'))
        tax_percent = validated_data.get('tax_percent', Decimal('0.00'))

        tax_amount = (subtotal_amount - discount_amount) * (tax_percent / Decimal('100.00'))
        total_amount = subtotal_amount - discount_amount + tax_amount

        # --- START: Generate Invoice Number ---
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        # --- END: Generate Invoice Number ---

        invoice_data = {
            'customer_id': validated_data['customer_id'],
            'user_id': current_user_id,
            'invoice_number': invoice_number, # Add invoice_number to data
            'due_date': validated_data.get('due_date'),
            'subtotal_amount': subtotal_amount,
            'discount_amount': discount_amount,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': validated_data.get('status', 'Pending')
        }

        invoice_id = Invoice.create(invoice_data)
        if not invoice_id:
            return error_response(error_code='server_error', message="Failed to create the invoice record.", status=500)

        for item in validated_data['items']:
            Invoice.add_item(invoice_id, item['product_id'], item['quantity'])

        # Handle initial payment if provided
        if 'initial_payment' in validated_data:
            payment_info = validated_data['initial_payment']
            Payment.record_payment(
                invoice_id=invoice_id,
                amount=payment_info['amount'],
                method=payment_info['method'],
                reference_no=payment_info.get('reference_no')
            )
            # Check if invoice is fully paid and update status
            if Decimal(payment_info['amount']) >= total_amount:
                Invoice.update_status(invoice_id, 'Paid')

        created_invoice = Invoice.find_by_id(invoice_id)
        return success_response(data=created_invoice.to_dict(), status=201)

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while creating the invoice.', details=str(e), status=500)

# ... (rest of the file remains the same) ...

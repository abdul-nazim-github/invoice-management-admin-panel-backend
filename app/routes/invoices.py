from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.invoice_schema import invoice_schema
from app.utils.error_messages import ERROR_MESSAGES
from app.database.models.invoice import Invoice
from app.database.models.invoice_item_model import InvoiceItem
from app.database.models.product import Product
from app.database.models.customer import Customer
from app.database.models.payment import Payment
from decimal import Decimal
from datetime import datetime, date
from app.utils.auth import require_admin
from app.utils.response import success_response, error_response

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
        customer = Customer.find_by_id(validated_data['customer_id'])
        if not customer:
            return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["customer"], status=404)

        subtotal_amount = Decimal('0.00')
        for item in validated_data['items']:
            product = Product.find_by_id(item['product_id'])
            if not product:
                return error_response(error_code='not_found', message=f"Product with ID {item['product_id']} not found.", status=404)
            subtotal_amount += Decimal(product.price) * Decimal(item['quantity'])

        current_user_id = get_jwt_identity()
        discount_amount = Decimal(validated_data.get('discount_amount', '0.00'))
        tax_percent = Decimal(validated_data.get('tax_percent', '0.00'))

        tax_amount = (subtotal_amount - discount_amount) * (tax_percent / Decimal('100.00'))
        total_amount = subtotal_amount - discount_amount + tax_amount
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        invoice_data = {
            'customer_id': validated_data['customer_id'],
            'user_id': current_user_id,
            'invoice_number': invoice_number,
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
            product = Product.find_by_id(item['product_id'])
            item_data = {
                'invoice_id': invoice_id,
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': product.price
            }
            InvoiceItem.create(item_data)
            # Update the stock for the product
            Product.update_stock(item['product_id'], -item['quantity'])

        if 'initial_payment' in validated_data and validated_data['initial_payment']:
            payment_info = validated_data['initial_payment']
            Payment.record_payment(
                invoice_id=invoice_id,
                amount=Decimal(payment_info['amount']),
                payment_date=date.today(),
                method=payment_info['method'],
                reference_no=payment_info.get('reference_no')
            )

        created_invoice = Invoice.find_by_id(invoice_id)
        return success_response(result=created_invoice.to_dict(), status=201)

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while creating the invoice.', details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_invoice(invoice_id):
    data = request.get_json()
    if not data:
        return error_response(error_code='validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        validated_data = invoice_schema.load(data)
    except ValidationError as err:
        return error_response(error_code='validation_error', message="The provided data is invalid.", details=err.messages, status=400)

    try:
        invoice = Invoice.find_by_id(invoice_id)
        if not invoice:
            return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

        old_items = InvoiceItem.find_by_invoice_id(invoice_id)
        old_items_map = {item.product_id: item for item in old_items}
        new_items = validated_data['items']

        # Calculate stock changes
        for item_data in new_items:
            product_id = item_data['product_id']
            new_quantity = item_data['quantity']

            if product_id in old_items_map:
                old_quantity = old_items_map[product_id].quantity
                quantity_diff = old_quantity - new_quantity
                Product.update_stock(product_id, quantity_diff)
                del old_items_map[product_id]
            else:
                Product.update_stock(product_id, -new_quantity)

        # For items that were removed, add their quantities back to the stock
        for old_item in old_items_map.values():
            Product.update_stock(old_item.product_id, old_item.quantity)

        # Update invoice and items
        InvoiceItem.delete_by_invoice_id(invoice_id)
        for item_data in new_items:
            product = Product.find_by_id(item_data['product_id'])
            new_item_data = {
                'invoice_id': invoice_id,
                'product_id': item_data['product_id'],
                'quantity': item_data['quantity'],
                'price': product.price
            }
            InvoiceItem.create(new_item_data)

        # Recalculate totals
        subtotal_amount = sum(Decimal(Product.find_by_id(item['product_id']).price) * Decimal(item['quantity']) for item in new_items)
        discount_amount = Decimal(validated_data.get('discount_amount', '0.00'))
        tax_percent = Decimal(validated_data.get('tax_percent', '0.00'))
        tax_amount = (subtotal_amount - discount_amount) * (tax_percent / Decimal('100.00'))
        total_amount = subtotal_amount - discount_amount + tax_amount

        # Determine invoice status based on payments
        payments = Payment.find_by_invoice_id(invoice_id)
        total_paid = sum(p.amount for p in payments)

        new_status = 'Pending'
        if total_paid >= total_amount:
            new_status = 'Paid'
        elif total_paid > 0:
            new_status = 'Partially Paid'

        invoice_data = {
            'customer_id': validated_data['customer_id'],
            'due_date': validated_data.get('due_date'),
            'subtotal_amount': subtotal_amount,
            'discount_amount': discount_amount,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': new_status
        }
        Invoice.update(invoice_id, invoice_data)

        updated_invoice = Invoice.find_by_id(invoice_id)
        return success_response(result=updated_invoice.to_dict(), status=200)

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while updating the invoice.', details=str(e), status=500)

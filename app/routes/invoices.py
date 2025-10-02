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
from app.utils.pagination import get_pagination

invoices_blueprint = Blueprint('invoices', __name__)

@invoices_blueprint.route('/invoices', methods=['GET'])
@jwt_required()
def list_invoices():
    try:
        page, per_page = get_pagination()
        status = request.args.get('status')
        customer_id = request.args.get('customer_id')
        q = request.args.get('q')

        offset = (page - 1) * per_page
        invoices, total = Invoice.list_all(customer_id=customer_id, status=status, offset=offset, limit=per_page, q=q)

        return success_response(
            result=[invoice.to_dict() for invoice in invoices],
            meta={
                'total': total,
                'page': page,
                'per_page': per_page,
            },
            status=200
        )

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while fetching invoices.', details=str(e), status=500)

@invoices_blueprint.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    try:
        invoice = Invoice.find_by_id(invoice_id)
        if not invoice:
            return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

        customer = Customer.find_by_id(invoice.customer_id)
        invoice_items = InvoiceItem.find_by_invoice_id(invoice_id)
        payments = Payment.find_by_invoice_id(invoice_id)

        invoice_data = invoice.to_dict()
        invoice_data['customer'] = customer.to_dict() if customer else None
        invoice_data['items'] = [item.to_dict() for item in invoice_items]
        invoice_data['payments'] = [payment.to_dict() for payment in payments]

        return success_response(result=invoice_data, status=200)

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while fetching the invoice.', details=str(e), status=500)

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

        # Determine initial status
        initial_status = 'Pending'
        if 'initial_payment' in validated_data and validated_data['initial_payment']:
            initial_payment_amount = Decimal(validated_data['initial_payment']['amount'])
            if initial_payment_amount >= total_amount:
                initial_status = 'Paid'
            elif initial_payment_amount > 0:
                initial_status = 'Partially Paid'

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
            'status': initial_status
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

    invoice = Invoice.find_by_id(invoice_id)
    if not invoice:
        return error_response(error_code='not_found', message=ERROR_MESSAGES["not_found"]["invoice"], status=404)

    try:
        validated_data = invoice_schema.load(data, partial=True)
    except ValidationError as err:
        return error_response(error_code='validation_error', message="The provided data is invalid.", details=err.messages, status=400)

    try:
        # If items are being updated, handle stock changes and replace items.
        if 'items' in validated_data:
            old_items = InvoiceItem.find_by_invoice_id(invoice_id)
            old_items_map = {item.product_id: item.quantity for item in old_items}
            new_items_data = validated_data['items']
            new_items_map = {item['product_id']: item['quantity'] for item in new_items_data}
            
            all_product_ids = set(old_items_map.keys()) | set(new_items_map.keys())

            for pid in all_product_ids:
                old_qty = old_items_map.get(pid, 0)
                new_qty = new_items_map.get(pid, 0)
                if old_qty != new_qty:
                    quantity_diff = old_qty - new_qty
                    Product.update_stock(pid, quantity_diff)

            InvoiceItem.delete_by_invoice_id(invoice_id)
            for item_data in new_items_data:
                product = Product.find_by_id(item_data['product_id'])
                InvoiceItem.create({
                    'invoice_id': invoice_id,
                    'product_id': item_data['product_id'],
                    'quantity': item_data['quantity'],
                    'price': product.price
                })

        # Recalculate totals if financial fields have changed.
        recalculate = 'items' in validated_data or 'discount_amount' in validated_data or 'tax_percent' in validated_data
        if recalculate:
            current_items = InvoiceItem.find_by_invoice_id(invoice_id)
            subtotal_amount = sum(item.price * item.quantity for item in current_items)
            
            discount_amount = Decimal(validated_data.get('discount_amount', invoice.discount_amount))
            tax_percent = Decimal(validated_data.get('tax_percent', invoice.tax_percent))
            
            tax_amount = (subtotal_amount - discount_amount) * (tax_percent / Decimal('100.00'))
            total_amount = subtotal_amount - discount_amount + tax_amount

            validated_data['subtotal_amount'] = subtotal_amount
            validated_data['discount_amount'] = discount_amount
            validated_data['tax_percent'] = tax_percent
            validated_data['tax_amount'] = tax_amount
            validated_data['total_amount'] = total_amount
        else:
            total_amount = invoice.total_amount

        # Always re-evaluate status
        payments = Payment.find_by_invoice_id(invoice_id)
        total_paid = sum(p.amount for p in payments)

        if total_paid >= total_amount:
            validated_data['status'] = 'Paid'
        elif total_paid > 0:
            validated_data['status'] = 'Partially Paid'
        else:
            validated_data['status'] = 'Pending'

        # Remove 'items' as it's not a direct column in the 'invoices' table
        validated_data.pop('items', None)

        # Update the invoice record
        if validated_data:
            Invoice.update(invoice_id, validated_data)

        # Fetch and return the fully updated invoice
        updated_invoice = Invoice.find_by_id(invoice_id)
        customer = Customer.find_by_id(updated_invoice.customer_id)
        invoice_items = InvoiceItem.find_by_invoice_id(invoice_id)
        payments = Payment.find_by_invoice_id(invoice_id)

        updated_invoice_data = updated_invoice.to_dict()
        updated_invoice_data['customer'] = customer.to_dict() if customer else None
        updated_invoice_data['items'] = [item.to_dict() for item in invoice_items]
        updated_invoice_data['payments'] = [payment.to_dict() for payment in payments]

        return success_response(result=updated_invoice_data, status=200)

    except Exception as e:
        return error_response(error_code='server_error', message='An unexpected error occurred while updating the invoice.', details=str(e), status=500)


from .base_model import BaseModel
from datetime import datetime, date
from app.database.base import get_db_connection
from decimal import Decimal

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoices = getattr(self, 'invoices', [])
        self.aggregates = getattr(self, 'aggregates', {})

    def to_dict(self):
        d = super().to_dict()
        d.pop('invoices', None)
        d.pop('aggregates', None)
        d['full_name'] = d.pop('name', None)
        return d

    @classmethod
    def create(cls, data):
        """
        Overrides the base create method.
        """
        return super().create(data)

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        db = cls._get_db_manager()
        row = db.find_one_where("LOWER(email) = %s", (email.lower(),), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_id_with_aggregates(cls, customer_id, include_deleted=False):
        customer = cls.find_by_id(customer_id, include_deleted)
        if not customer:
            return None

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # This query calculates financial totals and counts invoices by status
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(total_amount), 0) as total_billed,
                        COALESCE(SUM(CASE WHEN status = 'Paid' THEN total_amount ELSE 0 END), 0) as total_paid,
                        COUNT(*) as total_invoices_all_types,
                        SUM(CASE WHEN status NOT IN ('Draft', 'Cancelled') THEN 1 ELSE 0 END) as active_invoices_count,
                        SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as paid_invoices_count,
                        SUM(CASE WHEN status IN ('Pending', 'Sent') AND due_date < CURDATE() THEN 1 ELSE 0 END) as overdue_invoices_count,
                        SUM(CASE WHEN status IN ('Pending', 'Sent') THEN 1 ELSE 0 END) as pending_payment_count
                    FROM invoices
                    WHERE customer_id = %s AND deleted_at IS NULL
                """, (customer_id,))
                
                stats = cursor.fetchone() or {}
        finally:
            conn.close()

        # Financial Aggregates
        total_billed = stats.get('total_billed', Decimal('0.0'))
        total_paid = stats.get('total_paid', Decimal('0.0'))
        total_due = total_billed - total_paid

        # Status Calculation
        total_invoices_all_types = stats.get('total_invoices_all_types', 0)
        active_invoices_count = stats.get('active_invoices_count', 0)
        paid_invoices_count = stats.get('paid_invoices_count', 0)
        overdue_invoices_count = stats.get('overdue_invoices_count', 0)
        pending_payment_count = stats.get('pending_payment_count', 0)

        customer_status = 'New'  # Default status
        if total_invoices_all_types > 0:
            if overdue_invoices_count > 0:
                customer_status = 'Overdue'
            elif pending_payment_count > 0:
                customer_status = 'Pending'
            elif active_invoices_count > 0 and active_invoices_count == paid_invoices_count:
                customer_status = 'Paid'

        customer.aggregates = {
            'total_billed': str(total_billed),
            'total_paid': str(total_paid),
            'total_due': str(total_due),
        }
        customer.status = customer_status
        
        return customer

    @classmethod
    def list_all(cls, q=None, status=None, offset=0, limit=20, customer_id=None, include_deleted=False):
        db = cls._get_db_manager()
        items, total = db.get_paginated(page=(offset // limit) + 1, per_page=limit, include_deleted=include_deleted)
        return [cls.from_row(i) for i in items], total

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0
        db = cls._get_db_manager()
        deleted_count = 0
        for customer_id in ids:
            if db.delete(customer_id, soft_delete=True):
                deleted_count += 1
        return deleted_count

    @classmethod
    def restore(cls, id):
        return False

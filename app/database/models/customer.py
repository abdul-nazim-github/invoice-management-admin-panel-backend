from .base_model import BaseModel
from app.database.db_manager import DBManager
from datetime import datetime, date

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoices = getattr(self, 'invoices', [])
        self.aggregates = getattr(self, 'aggregates', {})
        self.status = getattr(self, 'status', 'new') 

    def to_dict(self):
        """Serializes the Customer object to a dictionary, keeping original field names."""
        d = super().to_dict()
        # These complex objects are handled by the schema, not the basic model dict.
        d.pop('invoices', None) 
        d.pop('aggregates', None)
        return d

    @classmethod
    def create(cls, data):
        if 'status' not in data:
            data['status'] = 'new'
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

        db = DBManager()

        billed_query = "SELECT SUM(total_amount) as total FROM invoices WHERE customer_id = %s"
        billed_result = db.fetch_one_raw(billed_query, (customer_id,))
        total_billed = billed_result['total'] if billed_result and billed_result['total'] is not None else 0

        paid_query = "SELECT SUM(amount) as total FROM payments WHERE customer_id = %s"
        paid_result = db.fetch_one_raw(paid_query, (customer_id,))
        total_paid = paid_result['total'] if paid_result and paid_result['total'] is not None else 0

        invoices_query = "SELECT * FROM invoices WHERE customer_id = %s ORDER BY invoice_date DESC"
        invoices = db.fetch_all_raw(invoices_query, (customer_id,))

        customer.aggregates = {
            'total_billed': total_billed,
            'total_paid': total_paid,
            'total_due': total_billed - total_paid
        }
        customer.invoices = invoices if invoices else []

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
        """Restores a soft-deleted customer."""
        db = cls._get_db_manager()
        return db.restore(id)

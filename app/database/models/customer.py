from .base_model import BaseModel
from datetime import datetime, date

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Default values for attributes that might not be in every query
        self.invoices = getattr(self, 'invoices', [])
        self.aggregates = getattr(self, 'aggregates', {})
        self.status = getattr(self, 'status', 'active') # Ensure status has a default

    def to_dict(self):
        """Serializes the Customer object to a dictionary."""
        d = super().to_dict()
        d.pop('invoices', None) # Don't include nested lists by default
        d.pop('aggregates', None)
        d['full_name'] = d.pop('name', None) # Rename for consistency
        return d

    @classmethod
    def create(cls, data):
        """
        Overrides the base create method to ensure a status is always set.
        """
        if 'status' not in data:
            data['status'] = 'active'
        return super().create(data)

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        """Finds a customer by email, case-insensitively."""
        db = cls._get_db_manager()
        row = db.find_one_where("LOWER(email) = %s", (email.lower(),), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_id_with_aggregates(cls, customer_id, include_deleted=False):
        """Retrieves a customer with their invoices and financial aggregates."""
        # TODO: This method needs to be re-implemented with proper invoice/payment queries.
        # For now, it will just fetch the customer and return empty aggregates.
        customer = cls.find_by_id(customer_id, include_deleted)
        if customer:
            customer.aggregates = {
                'total_billed': 0,
                'total_paid': 0,
                'total_due': 0,
                'invoices': []
            }
        return customer

    @classmethod
    def list_all(cls, q=None, status=None, offset=0, limit=20, customer_id=None, include_deleted=False):
        """Lists all customers with filtering and pagination."""
        db = cls._get_db_manager()
        items, total = db.get_paginated(page=(offset // limit) + 1, per_page=limit, include_deleted=include_deleted)
        return [cls.from_row(i) for i in items], total

    @classmethod
    def bulk_soft_delete(cls, ids):
        """Soft deletes multiple customers by their IDs."""
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
        # This requires a custom query not yet in DBManager.
        # TODO: Add an `undelete` or `restore` method to DBManager.
        return False

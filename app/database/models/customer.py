from .base_model import BaseModel
from datetime import datetime, date

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Default values for attributes that might not be in every query
        self.invoices = getattr(self, 'invoices', [])
        self.aggregates = getattr(self, 'aggregates', {})

    def to_dict(self):
        """Serializes the Customer object to a dictionary."""
        created_at_iso = self.created_at.isoformat() if hasattr(self, 'created_at') and isinstance(self.created_at, (datetime, date)) else None
        updated_at_iso = self.updated_at.isoformat() if hasattr(self, 'updated_at') and isinstance(self.updated_at, (datetime, date)) else None

        return {
            'id': self.id,
            'full_name': getattr(self, 'name', None), # Use getattr for safety
            'email': getattr(self, 'email', None),
            'phone': getattr(self, 'phone', None),
            'address': getattr(self, 'address', None),
            'gst_number': getattr(self, 'gst_number', None),
            'created_at': created_at_iso,
            'updated_at': updated_at_iso,
            'status': getattr(self, 'status', 'New'), # Default status to 'New'
            'aggregates': self.aggregates
        }

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        """Finds a customer by email, case-insensitively."""
        db = cls._get_db_manager()
        # Use LOWER() for case-insensitive search to be DB compatible
        row = db.find_one_where("LOWER(email) = %s", (email.lower(),), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_id_with_aggregates(cls, customer_id, include_deleted=False):
        """Retrieves a customer with their invoices and financial aggregates."""
        db = cls._get_db_manager()

        # This method requires complex, custom queries that don't fit the generic manager methods.
        # We will need to implement generic query execution in the DBManager or handle it here.
        # For now, this method will be stubbed out to prevent errors.
        # TODO: Re-implement this method with a more robust query solution.
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
        # TODO: Re-implement this method with a more robust query solution.
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
        # For now, this method is stubbed.
        # TODO: Add an `undelele` or `restore` method to DBManager.
        return False

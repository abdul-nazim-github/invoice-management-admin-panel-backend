from .base_model import BaseModel
from app.database.db_manager import DBManager

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, id, full_name, email, phone, address, gst_number, status, **kwargs):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.address = address
        self.gst_number = gst_number
        self.status = status
        # Absorb any extra columns
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'status': self.status
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0

        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET status = 'deleted' WHERE id IN ({placeholders}) AND status != 'deleted'"
        
        # DBManager.execute_write_query returns the last inserted ID, but for an UPDATE, we can consider it the row count.
        # However, the previous implementation returned rowcount, so we'll just return a success/fail indicator or the number of IDs.
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)


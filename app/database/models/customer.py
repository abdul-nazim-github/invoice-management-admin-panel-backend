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
    def search(cls, search_term, include_deleted=False):
        """Searches for customers by full_name, email, or phone."""
        search_fields = ['full_name', 'email', 'phone']
        return super().search(search_term, search_fields, include_deleted)

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0

        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET status = 'deleted' WHERE id IN ({placeholders}) AND status != 'deleted'"
        
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)


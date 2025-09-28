from .base_model import BaseModel
from datetime import datetime

class Product(BaseModel):
    _table_name = 'products'

    def __init__(self, id, product_code, name, description, price, stock, **kwargs):
        self.id = id
        self.product_code = product_code
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        
        # Absorb any extra columns that might be in the database row
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Ensure timestamps are datetime objects
        if hasattr(self, 'created_at') and self.created_at and isinstance(self.created_at, str):
            self.created_at = datetime.strptime(self.created_at, '%Y-%m-%d %H:%M:%S')
        
        if hasattr(self, 'updated_at') and self.updated_at and isinstance(self.updated_at, str):
            self.updated_at = datetime.strptime(self.updated_at, '%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            'id': self.id,
            'product_code': self.product_code,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),  # Cast DECIMAL to float for JSON serialization
            'stock': self.stock,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def search(cls, search_term, include_deleted=False):
        """Searches for products by product_code or name.""" 
        search_fields = ['product_code', 'name']
        return super().search(search_term, search_fields, include_deleted)

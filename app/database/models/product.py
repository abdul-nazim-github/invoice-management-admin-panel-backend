from .base_model import BaseModel

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

    def to_dict(self):
        return {
            'id': self.id,
            'product_code': self.product_code,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),  # Cast DECIMAL to float for JSON serialization
            'stock': self.stock
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


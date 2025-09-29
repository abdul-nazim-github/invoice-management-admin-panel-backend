
from .base_model import BaseModel
from app.utils.utils import generate_unique_product_code

class Product(BaseModel):
    _table_name = 'products'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, row):
        """
        Creates a Product instance from a database row.
        """
        return cls(**row)

    @classmethod
    def create(cls, data):
        """
        Overrides the base create method to auto-generate a unique product_code.
        """
        if 'name' in data:
            data['product_code'] = generate_unique_product_code(data['name'])
        else:
            # As a fallback if name is not provided, though 'name' is required by schema
            data['product_code'] = generate_unique_product_code('Product')
        
        return super().create(data)

    @classmethod
    def search(cls, search_term, include_deleted=False):
        """
        Searches for products by product_code or name.
        """
        # Placeholder for search functionality
        # A full implementation would require a dedicated search method in the DBManager
        return [], 0

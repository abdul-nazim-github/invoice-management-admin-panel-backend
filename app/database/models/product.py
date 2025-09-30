from .base_model import BaseModel
from app.utils.utils import generate_unique_product_code
from decimal import Decimal
from app.database.db_manager import DBManager

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
        Overrides the base create method to auto-generate a unique product_code
        and ensure the price is correctly quantized to two decimal places.
        """
        if 'name' in data:
            data['product_code'] = generate_unique_product_code(data['name'])
        else:
            # As a fallback if name is not provided, though 'name' is required by schema
            data['product_code'] = generate_unique_product_code('Product')
        
        if 'price' in data and data['price'] is not None:
            data['price'] = Decimal(data['price']).quantize(Decimal('0.00'))

        return super().create(data)

    @classmethod
    def update_stock(cls, product_id, quantity_change):
        """
        Updates the stock for a given product.
        `quantity_change` is the amount to add to the stock (can be negative).
        """
        query = f"UPDATE {cls._table_name} SET stock = stock + %s WHERE id = %s"
        params = (quantity_change, product_id)
        DBManager.execute_write_query(query, params)

    @classmethod
    def search(cls, search_term, include_deleted=False):
        """
        Searches for products by product_code or name.
        """
        # Placeholder for search functionality
        # A full implementation would require a dedicated search method in the DBManager
        return [], 0

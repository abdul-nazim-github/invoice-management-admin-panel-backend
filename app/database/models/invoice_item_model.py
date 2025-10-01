from .base_model import BaseModel
from app.database.db_manager import DBManager
from decimal import Decimal

class InvoiceItem(BaseModel):
    _table_name = 'invoice_items'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        price_float = float(self.price)
        total_float = float(self.total)
        
        product_details = {
            'id': self.product_id,
            'name': getattr(self, 'product_name', None),
            'product_code': getattr(self, 'product_code', None),
            'description': getattr(self, 'product_description', None),
            'stock': getattr(self, 'stock', None)
        }

        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'quantity': self.quantity,
            'price': price_float,
            'total': total_float,
            'product': product_details
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def find_by_invoice_id(cls, invoice_id):
        query = """
            SELECT
                ii.id, ii.invoice_id, ii.product_id, ii.quantity, ii.price, ii.total,
                p.name as product_name, p.product_code, p.description as product_description, p.stock
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = %s
        """
        params = (invoice_id,)
        rows = DBManager.execute_query(query, params, fetch='all')
        return [cls.from_row(row) for row in rows] if rows else []

    @classmethod
    def delete_by_invoice_id(cls, invoice_id):
        query = f"DELETE FROM {cls._table_name} WHERE invoice_id = %s"
        params = (invoice_id,)
        DBManager.execute_write_query(query, params)

    @classmethod
    def create(cls, data):
        quantity = Decimal(data['quantity'])
        price = Decimal(data['price'])
        total = quantity * price

        query = f"INSERT INTO {cls._table_name} (invoice_id, product_id, quantity, price, total) VALUES (%s, %s, %s, %s, %s)"
        params = (data['invoice_id'], data['product_id'], quantity, price, total)
        
        item_id = DBManager.execute_write_query(query, params)
        return item_id

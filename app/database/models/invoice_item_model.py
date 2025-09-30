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
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': int(price_float) if price_float.is_integer() else price_float,
            'total': int(total_float) if total_float.is_integer() else total_float
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def find_by_invoice_id(cls, invoice_id):
        query = f"SELECT * FROM {cls._table_name} WHERE invoice_id = %s"
        params = (invoice_id,)
        rows = DBManager.execute_query(query, params, fetch='all')
        return [cls.from_row(row) for row in rows]

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

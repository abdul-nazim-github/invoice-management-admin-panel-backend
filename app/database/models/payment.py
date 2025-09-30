from .base_model import BaseModel
from app.database.db_manager import DBManager
from decimal import Decimal
from datetime import date
from app.database.models.invoice import Invoice

class Payment(BaseModel):
    _table_name = 'payments'

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat() if isinstance(self.payment_date, date) else None,
            'method': self.method,
            'reference_no': self.reference_no
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def record_payment(cls, invoice_id, amount, method, payment_date=None, reference_no=None):
        # Ensure amount is a Decimal with two places
        amount_decimal = Decimal(amount).quantize(Decimal('0.00'))
        
        # Default to today's date if not provided
        if payment_date is None:
            payment_date = date.today()

        query = """
            INSERT INTO payments (invoice_id, amount, payment_date, method, reference_no) 
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (invoice_id, amount_decimal, payment_date, method, reference_no)
        
        payment_id = DBManager.execute_write_query(query, params)

        return payment_id

    @classmethod
    def find_by_id(cls, payment_id):
        query = f"SELECT * FROM {cls._table_name} WHERE id = %s"
        row = DBManager.execute_query(query, (payment_id,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def find_by_invoice_id(cls, invoice_id):
        query = f"SELECT * FROM {cls._table_name} WHERE invoice_id = %s ORDER BY payment_date DESC"
        rows = DBManager.execute_query(query, (invoice_id,), fetch='all')
        return [cls.from_row(row) for row in rows] if rows else []

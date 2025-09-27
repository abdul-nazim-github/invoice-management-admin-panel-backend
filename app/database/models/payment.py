from .base_model import BaseModel
from datetime import date

class Payment(BaseModel):
    _table_name = 'payments'

    def __init__(self, id, invoice_id, amount, payment_date, method, reference_no=None, **kwargs):
        self.id = id
        self.invoice_id = invoice_id
        self.amount = amount
        self.payment_date = payment_date
        self.method = method
        self.reference_no = reference_no
        # Absorb any extra columns
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'amount': float(self.amount), # Cast DECIMAL to float
            'payment_date': self.payment_date.isoformat() if isinstance(self.payment_date, date) else self.payment_date,
            'method': self.method,
            'reference_no': self.reference_no
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    # create, update, find_all, find_by_id, and soft_delete are inherited from BaseModel

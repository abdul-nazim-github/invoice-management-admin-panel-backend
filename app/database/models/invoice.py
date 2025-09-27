from .base_model import BaseModel
from datetime import date

class Invoice(BaseModel):
    _table_name = 'invoices'

    def __init__(self, id, invoice_number, customer_id, user_id, invoice_date, total_amount, status, due_date=None, **kwargs):
        self.id = id
        self.invoice_number = invoice_number
        self.customer_id = customer_id
        self.user_id = user_id
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.total_amount = total_amount
        self.status = status
        # Absorb any extra columns
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'invoice_date': self.invoice_date.isoformat() if isinstance(self.invoice_date, date) else self.invoice_date,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, date) else self.due_date,
            'total_amount': float(self.total_amount), # Cast DECIMAL to float
            'status': self.status
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    # create, update, find_all, find_by_id, and soft_delete are inherited from BaseModel

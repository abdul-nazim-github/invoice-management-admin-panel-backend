from .base_model import BaseModel
from app.database.db_manager import DBManager

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
            'amount': str(self.amount),
            'payment_date': self.payment_date.isoformat(),
            'method': self.method,
            'reference_no': self.reference_no
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def search(cls, search_term, include_deleted=False):
        """Searches for payments by reference_no or method."""
        search_fields = ['reference_no', 'method']
        return super().search(search_term, search_fields, include_deleted)


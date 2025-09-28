from .base_model import BaseModel
from app.database.db_manager import DBManager
from decimal import Decimal
from datetime import datetime

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        # Dynamically set attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Ensure essential attributes are present
        self.invoices = getattr(self, 'invoices', [])
        self.aggregates = getattr(self, 'aggregates', {})

    def to_dict(self):
        """Converts the customer object to a dictionary with nested aggregates and invoices."""
        return {
            'id': self.id,
            'full_name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'status': self.payment_status,
            'invoice_count': self.invoice_count,
            'aggregates': self.aggregates
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def find_by_id_with_aggregates(cls, customer_id, include_deleted=False):
        """
        Fetches a customer by their ID and includes aggregated financial data and
        a list of their invoices.
        """
        # SQL to fetch customer details and high-level aggregates
        customer_query = f"""
            SELECT
                c.*,
                COUNT(i.id) AS invoice_count,
                COALESCE(SUM(i.total_amount), 0) AS total_billed,
                CASE
                    WHEN COUNT(i.id) = 0 THEN 'New'
                    WHEN SUM(CASE WHEN i.status = 'Pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                    WHEN SUM(CASE WHEN i.status = 'Pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                    ELSE 'Paid'
                END AS payment_status
            FROM {cls._table_name} c
            LEFT JOIN invoices i ON c.id = i.customer_id AND i.deleted_at IS NULL
            WHERE c.id = %s
        """
        if not include_deleted:
            customer_query += " AND c.deleted_at IS NULL"
        
        customer_query += " GROUP BY c.id"
        
        customer_row = DBManager.execute_query(customer_query, (customer_id,), fetch='one')
        if not customer_row:
            return None

        # SQL to fetch all invoices for the customer
        invoices_query = """
            SELECT 
                i.id, i.invoice_number, i.due_date, i.total_amount, i.created_at, i.status,
                (i.total_amount - COALESCE(SUM(p.amount), 0)) as due_amount
            FROM invoices i
            LEFT JOIN payments p ON i.id = p.invoice_id
            WHERE i.customer_id = %s
        """
        if not include_deleted:
            invoices_query += " AND i.deleted_at IS NULL"
        
        invoices_query += " GROUP BY i.id ORDER BY i.created_at DESC"
        
        invoices_rows = DBManager.execute_query(invoices_query, (customer_id,), fetch='all')

        # Calculate total paid across all invoices
        total_paid_query = """
            SELECT COALESCE(SUM(p.amount), 0) as total_paid
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            WHERE i.customer_id = %s
        """
        total_paid_row = DBManager.execute_query(total_paid_query, (customer_id,), fetch='one')
        total_paid = total_paid_row['total_paid'] if total_paid_row else 0
        
        total_billed = customer_row['total_billed']
        total_due = total_billed - total_paid

        # Create the customer object
        customer = cls.from_row(customer_row)
        
        # Format invoices
        invoices_list = [
            {
                'id': row['id'],
                'invoice_number': row['invoice_number'],
                'due_date': row['due_date'].isoformat() if isinstance(row['due_date'], datetime) else row['due_date'],
                'total_amount': float(row['total_amount']),
                'created_at': row['created_at'].isoformat() if isinstance(row['created_at'], datetime) else row['created_at'],
                'status': row['status'],
                'due_amount': float(row['due_amount'])
            } for row in invoices_rows
        ]
        
        # Set aggregates and invoices
        customer.aggregates = {
            'total_billed': float(total_billed),
            'total_paid': float(total_paid),
            'total_due': float(total_due),
            'invoices': invoices_list
        }
        
        return customer


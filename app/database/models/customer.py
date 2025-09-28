from .base_model import BaseModel
from app.database.db_manager import DBManager
from decimal import Decimal
from datetime import datetime

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # Convert date strings to datetime objects upon instantiation
            if key in ('created_at', 'updated_at') and value and isinstance(value, str):
                try:
                    # Handle ISO format with or without 'T' separator
                    setattr(self, key, datetime.fromisoformat(value.replace(' ', 'T')))
                except (ValueError, TypeError):
                    # If parsing fails, keep the original string
                    setattr(self, key, value)
            else:
                setattr(self, key, value)
        
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
            'status': getattr(self, 'payment_status', None),
            'invoice_count': getattr(self, 'invoice_count', 0),
            'aggregates': self.aggregates
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def create(cls, data):
        allowed_fields = {'name', 'email', 'phone', 'address', 'gst_number'}
        filtered_data = {key: value for key, value in data.items() if key in allowed_fields}
        if not filtered_data:
            return None
        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["%s"] * len(filtered_data))
        query = f'INSERT INTO {cls._table_name} ({columns}) VALUES ({placeholders})'
        return DBManager.execute_write_query(query, tuple(filtered_data.values()))

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        query = f"SELECT * FROM {cls._table_name} WHERE email = %s"
        if not include_deleted:
            query += " AND deleted_at IS NULL"
        row = DBManager.execute_query(query, (email,), fetch='one')
        return cls.from_row(row)
    
    @classmethod
    def find_by_id(cls, id, include_deleted=False):
        """A simple find_by_id for internal use, like after creation."""
        query = f"SELECT * FROM {cls._table_name} WHERE id = %s"
        if not include_deleted:
            query += " AND deleted_at IS NULL"
        row = DBManager.execute_query(query, (id,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def find_by_id_with_aggregates(cls, customer_id, include_deleted=False):
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

        invoices_query = """
            SELECT 
                i.id, i.invoice_number, i.due_date, i.total_amount, i.created_at, i.status,
                (i.total_amount - COALESCE(SUM(p.amount), 0)) as due_amount
            FROM invoices i
            LEFT JOIN payments p ON i.id = p.invoice_id
            WHERE i.customer_id = %s AND i.deleted_at IS NULL
            GROUP BY i.id ORDER BY i.created_at DESC
        """
        invoices_rows = DBManager.execute_query(invoices_query, (customer_id,), fetch='all')

        total_paid_query = "SELECT COALESCE(SUM(p.amount), 0) as total_paid FROM payments p JOIN invoices i ON p.invoice_id = i.id WHERE i.customer_id = %s"
        total_paid_row = DBManager.execute_query(total_paid_query, (customer_id,), fetch='one')
        total_paid = total_paid_row['total_paid'] if total_paid_row else 0
        
        customer = cls.from_row(customer_row)
        total_billed = customer_row['total_billed']
        customer.aggregates = {
            'total_billed': float(total_billed),
            'total_paid': float(total_paid),
            'total_due': float(total_billed - total_paid),
            'invoices': [
                {
                    'id': row['id'],
                    'invoice_number': row['invoice_number'],
                    'due_date': row['due_date'].isoformat(),
                    'total_amount': float(row['total_amount']),
                    'created_at': row['created_at'].isoformat(),
                    'status': row['status'],
                    'due_amount': float(row['due_amount'])
                } for row in invoices_rows
            ]
        }
        return customer

    @classmethod
    def list_all(cls, q=None, status=None, offset=0, limit=20, customer_id=None, include_deleted=False):
        where = []
        params = []
        if not include_deleted:
            where.append("c.deleted_at IS NULL")
        if customer_id:
            where.append("c.id = %s")
            params.append(customer_id)
        if q:
            where.append("(c.name LIKE %s OR c.email LIKE %s OR c.phone LIKE %s)")
            like = f"%{q}%"
            params.extend([like, like, like])
        where_sql = " WHERE " + " AND ".join(where) if where else ""

        base_query = f"""
            SELECT 
                c.id, c.name, c.email, c.phone, c.address, c.gst_number, c.created_at, c.updated_at,
                CASE
                    WHEN COUNT(i.id) = 0 THEN 'New'
                    WHEN SUM(CASE WHEN i.status='pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                    WHEN SUM(CASE WHEN i.status='pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                    WHEN SUM(CASE WHEN i.status='paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                    ELSE 'New'
                END AS payment_status,
                COUNT(i.id) AS invoice_count
            FROM {cls._table_name} c
            LEFT JOIN invoices i ON c.id = i.customer_id AND i.deleted_at IS NULL
            {where_sql}
            GROUP BY c.id
        """

        outer_where = ""
        if status:
            outer_where = " WHERE sub.payment_status = %s"
        
        final_query = f"SELECT * FROM ({base_query}) AS sub {outer_where} ORDER BY sub.id DESC LIMIT %s OFFSET %s"
        
        pagination_params = params + ([status] if status else []) + [limit, offset]
        rows = DBManager.execute_query(final_query, tuple(pagination_params), fetch='all')
        customers = [cls.from_row(row) for row in rows] if rows else []

        count_query = f"SELECT COUNT(*) AS total FROM ({base_query}) AS sub {outer_where}"
        count_params = tuple(params + ([status] if status else []))
        result = DBManager.execute_query(count_query, count_params, fetch='one')
        total = result['total'] if result else 0

        return customers, total

    @classmethod
    def bulk__soft_delete(cls, ids):
        if not ids:
            return 0
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET deleted_at = NOW() WHERE id IN ({placeholders}) AND deleted_at IS NULL"
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)
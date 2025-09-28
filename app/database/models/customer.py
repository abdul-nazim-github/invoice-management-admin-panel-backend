from .base_model import BaseModel
from app.database.db_manager import DBManager
from decimal import Decimal

class Customer(BaseModel):
    _table_name = 'customers'

    def __init__(self, id, full_name, email, phone, address, gst_number, status, **kwargs):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.address = address
        self.gst_number = gst_number
        self.status = status
        # Absorb any extra columns, like invoice_count or payment_status if passed directly
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'status': self.status
        }
        # Add invoice_count and payment_status if they have been set on the instance
        if hasattr(self, 'invoice_count'):
            data['invoice_count'] = self.invoice_count
        if hasattr(self, 'payment_status'):
            data['payment_status'] = self.payment_status
        return data

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # The __init__ will handle all fields from the row dictionary
        return cls(**row)

    @classmethod
    def find_by_id(cls, id, include_deleted=False):
        """
        Overrides BaseModel.find_by_id to include the customer's payment status.
        """
        customers, _ = cls.list_all(customer_id=id, include_deleted=include_deleted)
        return customers[0] if customers else None

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        """Finds a customer by their email address (without payment status)."""
        query = f"SELECT * FROM {cls._table_name} WHERE email = %s"
        if not include_deleted:
            query += " AND status != 'deleted'"
        
        row = DBManager.execute_query(query, (email,), fetch='one')
        # Using the simplified from_row which is fine
        return cls.from_row(row)

    @classmethod
    def list_all(cls, q=None, status=None, offset=0, limit=20, customer_id=None, include_deleted=False):
        """
        A comprehensive method to list customers with filtering, searching, and pagination.
        """
        where = []
        params = []

        if not include_deleted:
            where.append("c.status != 'deleted'")

        if customer_id:
            where.append("c.id = %s")
            params.append(customer_id)

        if q:
            where.append("(c.full_name LIKE %s OR c.email LIKE %s OR c.phone LIKE %s)")
            like = f"%{q}%"
            params.extend([like, like, like])

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        # Base query to calculate status and invoice count
        base_query = f"""
            SELECT 
                c.id,
                c.full_name, 
                c.email, 
                c.phone,
                c.address,
                c.gst_number,
                c.created_at, 
                c.status,
                CASE
                    WHEN COUNT(i.id) = 0 THEN 'New'
                    WHEN SUM(CASE WHEN i.status='pending' AND i.due_date < NOW() THEN 1 ELSE 0 END) > 0 THEN 'Overdue'
                    WHEN SUM(CASE WHEN i.status='pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                    WHEN SUM(CASE WHEN i.status='paid' THEN 1 ELSE 0 END) = COUNT(i.id) THEN 'Paid'
                    ELSE 'New'
                END AS payment_status,
                COUNT(i.id) AS invoice_count
            FROM {cls._table_name} c
            LEFT JOIN invoices i ON c.id = i.customer_id AND i.status != 'deleted'
            {where_sql}
            GROUP BY c.id, c.full_name, c.email, c.phone, c.address, c.gst_number, c.created_at, c.status
        """

        outer_where = ""
        outer_params = list(params) # Create a copy for the outer query
        if status:
            outer_where = " WHERE sub.payment_status = %s"
            outer_params.append(status)

        # Final query for fetching the paginated/filtered list
        final_query = f"""
            SELECT * FROM ({base_query}) AS sub
            {outer_where}
            ORDER BY sub.id DESC
            LIMIT %s OFFSET %s
        """
        
        pagination_params = outer_params + [limit, offset]
        rows = DBManager.execute_query(final_query, tuple(pagination_params))
        
        customers = [cls.from_row(row) for row in rows] if rows else []

        # Count query for pagination
        count_query = f"SELECT COUNT(*) AS total FROM ({base_query}) AS sub {outer_where}"
        
        # We need to use the parameters for the base query and the outer where clause for the count
        count_params = tuple(params + ([status] if status else []))

        result = DBManager.execute_query(count_query, count_params, fetch='one')
        total = result['total'] if result else 0

        return customers, total

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0

        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET status = 'deleted' WHERE id IN ({placeholders}) AND status != 'deleted'"
        
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)

from .base_model import BaseModel
from app.database.db_manager import DBManager

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
        # Absorb any extra columns, including payment_status if passed directly
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
        # Add payment_status if it has been set on the instance
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
        status_filter = "" if include_deleted else f"AND c.status != 'deleted'"

        # This query joins with invoice data to calculate the payment status
        query = f"""
            SELECT c.*,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending' AND i.due_date < CURRENT_DATE
                    ) THEN 'Overdue'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Pending'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id
                    ) AND NOT EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Paid'
                    ELSE 'New'
                END as payment_status
            FROM {cls._table_name} c
            WHERE c.id = %s {status_filter}
        """
        
        row = DBManager.execute_query(query, (id,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def find_with_pagination_and_count(cls, page, per_page, include_deleted=False):
        """
        Overrides BaseModel.find_with_pagination_and_count to include payment status.
        """
        offset = (page - 1) * per_page
        
        status_filter = "" if include_deleted else f"WHERE c.status != 'deleted'"

        # The query is updated to calculate payment_status for each customer
        query = f"""
            SELECT c.*,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending' AND i.due_date < CURRENT_DATE
                    ) THEN 'Overdue'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Pending'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id
                    ) AND NOT EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Paid'
                    ELSE 'New'
                END as payment_status
            FROM {cls._table_name} c
            {status_filter}
            ORDER BY c.id
            LIMIT %s OFFSET %s
        """

        # The count query remains simple for performance
        count_query_filter = "WHERE status != 'deleted'" if not include_deleted else ""
        count_query = f"SELECT COUNT(*) FROM {cls._table_name} {count_query_filter}"

        rows = DBManager.execute_query(query, (per_page, offset))
        total_count_row = DBManager.execute_query(count_query, fetch='one')
        total = total_count_row['count'] if total_count_row else 0
        
        customers = [cls.from_row(row) for row in rows] if rows else []
        return customers, total

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
    def search(cls, search_term, include_deleted=False):
        """
        Overrides BaseModel.search to include the customer's payment status in search results.
        """
        search_fields = ['full_name', 'email', 'phone']
        search_conditions = ' OR '.join([f"c.{field} LIKE %s" for field in search_fields])
        search_values = tuple([f'%{search_term}%'] * len(search_fields))
        
        status_filter = "AND c.status != 'deleted'" if not include_deleted else ""
        
        # The search query is also updated to include payment_status
        query = f"""
            SELECT c.*,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending' AND i.due_date < CURRENT_DATE
                    ) THEN 'Overdue'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Pending'
                    WHEN EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id
                    ) AND NOT EXISTS (
                        SELECT 1 FROM invoices i
                        WHERE i.customer_id = c.id AND i.status = 'pending'
                    ) THEN 'Paid'
                    ELSE 'New'
                END as payment_status
            FROM {cls._table_name} c
            WHERE ({search_conditions}) {status_filter}
        """

        rows = DBManager.execute_query(query, search_values)
        return [cls.from_row(row) for row in rows] if rows else []

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0

        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET status = 'deleted' WHERE id IN ({placeholders}) AND status != 'deleted'"
        
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)

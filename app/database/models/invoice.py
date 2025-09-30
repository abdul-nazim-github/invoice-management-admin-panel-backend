from .base_model import BaseModel
from app.database.db_manager import DBManager
from datetime import datetime
from decimal import Decimal

class Invoice(BaseModel):
    _table_name = 'invoices'

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "invoice_number": self.invoice_number,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "total_amount": str(self.total_amount),
            "amount_paid": str(getattr(self, 'amount_paid', '0.00')),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def create(cls, data):
        # Quantize decimal fields before insertion
        for field in ['subtotal_amount', 'discount_amount', 'tax_amount', 'total_amount']:
            if field in data and data[field] is not None:
                data[field] = Decimal(data[field]).quantize(Decimal('0.00'))

        query = "INSERT INTO invoices (customer_id, user_id, invoice_number, due_date, subtotal_amount, discount_amount, tax_percent, tax_amount, total_amount, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (data['customer_id'], data['user_id'], data['invoice_number'], data['due_date'], data['subtotal_amount'], data['discount_amount'], data['tax_percent'], data['tax_amount'], data['total_amount'], data.get('status', 'Pending'))
        
        # DBManager.execute_write_query is expected to return the last inserted ID for MySQL.
        invoice_id = DBManager.execute_write_query(query, params)
        return invoice_id

    @classmethod
    def add_item(cls, invoice_id, product_id, quantity):
        query = "INSERT INTO invoice_items (invoice_id, product_id, quantity) VALUES (%s, %s, %s)"
        params = (invoice_id, product_id, quantity)
        DBManager.execute_write_query(query, params)

    @classmethod
    def find_by_id(cls, invoice_id, include_deleted=False):
        query = f"""
            SELECT i.*, COALESCE(SUM(p.amount), 0) as amount_paid
            FROM {cls._table_name} i
            LEFT JOIN payments p ON i.id = p.invoice_id
            WHERE i.id = %s
        """
        if not include_deleted:
            query += " AND i.deleted_at IS NULL"
        query += " GROUP BY i.id"
        row = DBManager.execute_query(query, (invoice_id,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def find_by_invoice_number(cls, invoice_number):
        query = "SELECT * FROM invoices WHERE invoice_number = %s AND deleted_at IS NULL"
        row = DBManager.execute_query(query, (invoice_number,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def list_all(cls, customer_id=None, status=None, offset=0, limit=10, q=None, include_deleted=False):
        where = []
        if not include_deleted:
            where.append("i.deleted_at IS NULL")

        params = []
        query_base = """ 
            SELECT i.*, c.name as customer_name, 
                   COALESCE(SUM(p.amount), 0) as amount_paid,
                   (i.total_amount - COALESCE(SUM(p.amount), 0)) as due_amount
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            LEFT JOIN payments p ON i.id = p.invoice_id
        """

        if customer_id:
            where.append("i.customer_id = %s")
            params.append(customer_id)
        if status:
            where.append("i.status = %s")
            params.append(status)
        if q:
            where.append("(i.invoice_number LIKE %s OR c.name LIKE %s)")
            like_q = f"%{q}%"
            params.extend([like_q, like_q])

        where_sql = " WHERE " + " AND ".join(where) if where else ""
        
        group_by_sql = " GROUP BY i.id, c.name ORDER BY i.id DESC LIMIT %s OFFSET %s"
        final_query = query_base + where_sql + group_by_sql
        params.extend([limit, offset])

        rows = DBManager.execute_query(final_query, tuple(params), fetch='all')
        invoices = [cls.from_row(row) for row in rows] if rows else []

        # Build the count query
        count_query_params = tuple(params[:-2]) # remove limit and offset
        count_query = "SELECT COUNT(DISTINCT i.id) as total FROM invoices i JOIN customers c ON i.customer_id = c.id" + where_sql
        
        count_result = DBManager.execute_query(count_query, count_query_params, fetch='one')
        total = count_result['total'] if count_result else 0

        return invoices, total
    
    @classmethod
    def update_status(cls, invoice_id, new_status):
        query = "UPDATE invoices SET status = %s, updated_at = NOW() WHERE id = %s"
        DBManager.execute_write_query(query, (new_status, invoice_id))

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET deleted_at = NOW() WHERE id IN ({placeholders}) AND deleted_at IS NULL"
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)

from .base_model import BaseModel
from app.database.db_manager import DBManager
from datetime import datetime, date
from decimal import Decimal

class Invoice(BaseModel):
    _table_name = 'invoices'

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            # Convert date/datetime strings from DB to objects upon instantiation
            if key in ('created_at', 'updated_at') and value and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace(' ', 'T'))
                except ValueError:
                    pass  # Keep original value if parsing fails
            elif key == 'due_date' and value and isinstance(value, str):
                try:
                    value = date.fromisoformat(value)
                except ValueError:
                    pass  # Keep original value if parsing fails

            setattr(self, key, value)

    def to_dict(self):
        total_amount_float = float(self.total_amount)
        amount_paid_float = float(getattr(self, 'amount_paid', '0.00'))
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "invoice_number": self.invoice_number,
            "created_at": self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            "due_date": self.due_date.isoformat() if hasattr(self, 'due_date') and self.due_date else None,
            "total_amount": int(total_amount_float) if total_amount_float.is_integer() else total_amount_float,
            "amount_paid": int(amount_paid_float) if amount_paid_float.is_integer() else amount_paid_float,
            "status": self.status,
            "updated_at": self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def create(cls, data):
        for field in ['subtotal_amount', 'discount_amount', 'tax_amount', 'total_amount']:
            if field in data and data[field] is not None:
                data[field] = Decimal(data[field]).quantize(Decimal('0.00'))

        query = "INSERT INTO invoices (customer_id, user_id, invoice_number, due_date, subtotal_amount, discount_amount, tax_percent, tax_amount, total_amount, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (data['customer_id'], data['user_id'], data['invoice_number'], data['due_date'], data['subtotal_amount'], data['discount_amount'], data['tax_percent'], data['tax_amount'], data['total_amount'], data.get('status', 'Pending'))
        
        invoice_id = DBManager.execute_write_query(query, params)
        return invoice_id

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

        count_query_params = tuple(params[:-2])
        count_query = "SELECT COUNT(DISTINCT i.id) as total FROM invoices i JOIN customers c ON i.customer_id = c.id" + where_sql
        
        count_result = DBManager.execute_query(count_query, count_query_params, fetch='one')
        total = count_result['total'] if count_result else 0

        return invoices, total
    
    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET deleted_at = NOW() WHERE id IN ({placeholders}) AND deleted_at IS NULL"
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)

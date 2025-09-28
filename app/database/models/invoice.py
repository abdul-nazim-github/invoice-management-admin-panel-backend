from .base_model import BaseModel
from app.database.db_manager import DBManager
from datetime import datetime

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
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def create(cls, data):
        query = "INSERT INTO invoices (customer_id, invoice_number, issue_date, due_date, total_amount, status) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (data['customer_id'], data['invoice_number'], data['issue_date'], data['due_date'], data['total_amount'], data.get('status', 'Pending'))
        return DBManager.execute_write_query(query, params)

    @classmethod
    def find_by_id(cls, invoice_id):
        query = "SELECT * FROM invoices WHERE id = %s AND deleted_at IS NULL"
        row = DBManager.execute_query(query, (invoice_id,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def find_by_invoice_number(cls, invoice_number):
        query = "SELECT * FROM invoices WHERE invoice_number = %s AND deleted_at IS NULL"
        row = DBManager.execute_query(query, (invoice_number,), fetch='one')
        return cls.from_row(row)

    @classmethod
    def list_all(cls, customer_id=None, status=None, offset=0, limit=10, q=None):
        where = ["i.deleted_at IS NULL"]
        params = []
        query_base = """ 
            SELECT i.*, c.name as customer_name, 
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

        count_query = "SELECT COUNT(DISTINCT i.id) as total FROM invoices i JOIN customers c ON i.customer_id = c.id" + where_sql
        count_params = tuple(params[:-2]) # remove limit and offset
        count_result = DBManager.execute_query(count_query, count_params, fetch='one')
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

class Payment(BaseModel):
    _table_name = 'payments'

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_row(cls, row):
        return cls(**row) if row else None

    @classmethod
    def record_payment(cls, payment_data):
        conn = DBManager.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if invoice exists
                cursor.execute("SELECT total_amount FROM invoices WHERE id = %s", (payment_data['invoice_id'],))
                invoice_row = cursor.fetchone()
                if not invoice_row:
                    raise ValueError("Invoice not found")
                invoice_total = invoice_row[0]

                # Insert payment
                query = "INSERT INTO payments (invoice_id, amount, payment_date, payment_method, notes) VALUES (%s, %s, %s, %s, %s)"
                params = (payment_data['invoice_id'], payment_data['amount'], payment_data['payment_date'], payment_data.get('payment_method', 'other'), payment_data.get('notes', ''))
                cursor.execute(query, params)
                payment_id = cursor.lastrowid

                # Update invoice status based on total payments
                if invoice_total is not None:
                    cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = %s", (payment_data['invoice_id'],))
                    total_paid_row = cursor.fetchone()
                    total_paid = total_paid_row[0] or 0
    
                    new_status = 'Pending'
                    if total_paid >= invoice_total:
                        new_status = 'Paid'
    
                    cursor.execute("UPDATE invoices SET status = %s WHERE id = %s", (new_status, payment_data['invoice_id']))
    
                conn.commit()
                return payment_id
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

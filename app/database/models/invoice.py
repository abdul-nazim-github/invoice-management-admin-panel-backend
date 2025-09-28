from .base_model import BaseModel
from app.database.db_manager import DBManager
from app.database.base import get_db_connection
from datetime import date, datetime

class Invoice(BaseModel):
    _table_name = 'invoices'

    def __init__(self, **kwargs):
        # Initialize all kwargs as instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.items = []  # Ensure items is always initialized

    def to_dict(self):
        # Convert all instance attributes to a dictionary
        invoice_dict = {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, date) else self.due_date,
            'subtotal_amount': float(self.subtotal_amount),
            'discount_amount': float(self.discount_amount),
            'tax_percent': float(self.tax_percent),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'status': self.status,
            'items': self.items,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and isinstance(self.created_at, datetime) else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and isinstance(self.updated_at, datetime) else None,
            'customer': {
                'id': self.customer_id,
                'name': self.customer_name,
                'email': self.customer_email
            },
            'user': {
                'id': self.user_id,
                'name': self.user_name,
                'email': self.user_email
            }
        }
        return invoice_dict

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def find_by_id(cls, invoice_id, include_deleted=False):
        query = f"""
            SELECT 
                i.*, 
                c.name as customer_name, c.email as customer_email,
                u.name as user_name, u.email as user_email
            FROM {cls._table_name} i
            JOIN customers c ON i.customer_id = c.id
            JOIN users u ON i.user_id = u.id
            WHERE i.id = %s
        """
        if not include_deleted:
            query += " AND i.deleted_at IS NULL"

        invoice_row = DBManager.execute_query(query, (invoice_id,), fetch='one')

        if not invoice_row:
            return None

        items_query = "SELECT product_id, quantity, unit_price FROM invoice_items WHERE invoice_id = %s"
        items_rows = DBManager.execute_query(items_query, (invoice_id,), fetch='all')

        invoice = cls.from_row(invoice_row)
        invoice.items = [{
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': float(item['unit_price'])
        } for item in items_rows]

        return invoice

    @classmethod
    def list_all(cls, q=None, status=None, offset=0, limit=20, include_deleted=False):
        where = []
        params = []

        if not include_deleted:
            where.append("i.deleted_at IS NULL")
        
        if status:
            where.append("i.status = %s")
            params.append(status)

        if q:
            where.append("(c.name LIKE %s OR c.email LIKE %s OR i.invoice_number LIKE %s)")
            like_query = f"%{q}%"
            params.extend([like_query, like_query, like_query])

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        query = f"""
            SELECT 
                i.*, 
                c.name as customer_name, c.email as customer_email,
                u.name as user_name, u.email as user_email
            FROM {cls._table_name} i
            JOIN customers c ON i.customer_id = c.id
            JOIN users u ON i.user_id = u.id
            {where_sql}
            ORDER BY i.id DESC
            LIMIT %s OFFSET %s
        """
        
        pagination_params = params + [limit, offset]
        rows = DBManager.execute_query(query, tuple(pagination_params), fetch='all')
        
        invoices = [cls.from_row(row) for row in rows] if rows else []

        count_query = f"""
            SELECT COUNT(*) as total
            FROM {cls._table_name} i
            JOIN customers c ON i.customer_id = c.id
            {where_sql}
        """
        
        result = DBManager.execute_query(count_query, tuple(params), fetch='one')
        total = result['total'] if result else 0

        return invoices, total

    @staticmethod
    def add_item(invoice_id, product_id, quantity):
        product_query = "SELECT price FROM products WHERE id = %s"
        product_row = DBManager.execute_query(product_query, (product_id,), fetch='one')

        if not product_row:
            raise ValueError(f"Product with ID {product_id} not found.")
        
        unit_price = product_row['price']

        query = "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)"
        DBManager.execute_write_query(query, (invoice_id, product_id, quantity, unit_price))

    @classmethod
    def bulk_soft_delete(cls, ids):
        if not ids:
            return 0

        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {cls._table_name} SET deleted_at = NOW() WHERE id IN ({placeholders}) AND deleted_at IS NULL"
        
        DBManager.execute_write_query(query, tuple(ids))
        return len(ids)

    @staticmethod
    def record_payment(payment_data):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Insert the payment record
                query = "INSERT INTO payments (invoice_id, payment_date, amount, method) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (payment_data['invoice_id'], payment_data['payment_date'], payment_data['amount'], payment_data['method']))
                payment_id = cursor.lastrowid

                # Update the invoice status based on the payment
                cursor.execute("SELECT total_amount FROM invoices WHERE id = %s", (payment_data['invoice_id'],))
                invoice_total_row = cursor.fetchone()
                if not invoice_total_row:
                    raise ValueError(f"Invoice with ID {payment_data['invoice_id']} not found.")
                invoice_total = invoice_total_row[0]

                cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = %s", (payment_data['invoice_id'],))
                total_paid_row = cursor.fetchone()
                total_paid = total_paid_row[0] or 0

                new_status = 'Pending'
                if total_paid >= invoice_total:
                    new_status = 'Paid'
                elif total_paid > 0:
                    new_status = 'Partially Paid'

                cursor.execute("UPDATE invoices SET status = %s WHERE id = %s", (new_status, payment_data['invoice_id']))

            conn.commit()
            return payment_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
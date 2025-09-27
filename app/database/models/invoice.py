from .base_model import BaseModel
from app.database.db_manager import DBManager
from app.database.base import get_db_connection
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
        self.items = [] # To hold invoice items
        # Absorb any extra columns
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        invoice_dict = {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'invoice_date': self.invoice_date.isoformat() if isinstance(self.invoice_date, date) else self.invoice_date,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, date) else self.due_date,
            'total_amount': float(self.total_amount), # Cast DECIMAL to float
            'status': self.status,
            'items': self.items # Include items in the dictionary
        }
        return invoice_dict

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    @classmethod
    def find_by_id(cls, invoice_id, include_deleted=False):
        query = f"SELECT * FROM {cls._table_name} WHERE id = %s"
        if not include_deleted:
            query += " AND status != 'deleted'"

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
    def search(cls, search_term, include_deleted=False):
        """Searches for invoices by customer_id or status."""
        search_fields = ['customer_id', 'status']
        return super().search(search_term, search_fields, include_deleted)

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
        query = f"UPDATE {cls._table_name} SET status = 'deleted' WHERE id IN ({placeholders}) AND status != 'deleted'"
        
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

                new_status = 'pending'
                if total_paid >= invoice_total:
                    new_status = 'paid'
                elif total_paid > 0:
                    new_status = 'partially_paid'

                cursor.execute("UPDATE invoices SET status = %s WHERE id = %s", (new_status, payment_data['invoice_id']))

            conn.commit()
            return payment_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
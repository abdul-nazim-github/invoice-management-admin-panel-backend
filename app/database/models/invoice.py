from .base import get_db_connection

class Invoice:
    @staticmethod
    def create(data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO invoices (customer_id, invoice_date, total_amount, status) VALUES (%s, %s, %s, %s)',
                (data['customer_id'], data['invoice_date'], data['total_amount'], data['status'])
            )
            conn.commit()
            return Invoice.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM invoices')
            return [Invoice.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(invoice_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM invoices WHERE id = %s', (invoice_id,))
            row = cursor.fetchone()
            if row:
                return Invoice.from_row(row)
            return None

    @staticmethod
    def update(invoice_id, data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE invoices SET customer_id = %s, invoice_date = %s, total_amount = %s, status = %s WHERE id = %s',
                (data['customer_id'], data['invoice_date'], data['total_amount'], data['status'], invoice_id)
            )
            conn.commit()
            return Invoice.get_by_id(invoice_id)

    @staticmethod
    def delete(invoice_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM invoices WHERE id = %s', (invoice_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        return {
            'id': row[0],
            'customer_id': row[1],
            'invoice_date': row[2],
            'total_amount': row[3],
            'status': row[4]
        }
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'invoice_date': self.invoice_date,
            'total_amount': self.total_amount,
            'status': self.status
        }

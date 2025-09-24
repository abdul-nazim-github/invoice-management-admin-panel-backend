from .base import get_db_connection

class Payment:
    @staticmethod
    def create(data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO payments (invoice_id, payment_date, amount, payment_method, status) VALUES (%s, %s, %s, %s, %s)',
                (data['invoice_id'], data['payment_date'], data['amount'], data['payment_method'], data['status'])
            )
            conn.commit()
            return Payment.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM payments')
            return [Payment.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(payment_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM payments WHERE id = %s', (payment_id,))
            row = cursor.fetchone()
            if row:
                return Payment.from_row(row)
            return None

    @staticmethod
    def update(payment_id, data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE payments SET invoice_id = %s, payment_date = %s, amount = %s, payment_method = %s, status = %s WHERE id = %s',
                (data['invoice_id'], data['payment_date'], data['amount'], data['payment_method'], data['status'], payment_id)
            )
            conn.commit()
            return Payment.get_by_id(payment_id)

    @staticmethod
    def delete(payment_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM payments WHERE id = %s', (payment_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        return {
            'id': row[0],
            'invoice_id': row[1],
            'payment_date': row[2],
            'amount': row[3],
            'payment_method': row[4],
            'status': row[5]
        }
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'payment_date': self.payment_date,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status
        }

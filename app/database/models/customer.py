from .base import get_db_connection

class Customer:
    @staticmethod
    def create(data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO customers (name, email, phone, address, gst_number, status) VALUES (%s, %s, %s, %s, %s, %s)',
                (data['name'], data['email'], data['phone'], data['address'], data['gst_number'], data['status'])
            )
            conn.commit()
            return Customer.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM customers')
            return [Customer.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(customer_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
            row = cursor.fetchone()
            if row:
                return Customer.from_row(row)
            return None

    @staticmethod
    def update(customer_id, data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE customers SET name = %s, email = %s, phone = %s, address = %s, gst_number = %s, status = %s WHERE id = %s',
                (data['name'], data['email'], data['phone'], data['address'], data['gst_number'], data['status'], customer_id)
            )
            conn.commit()
            return Customer.get_by_id(customer_id)

    @staticmethod
    def delete(customer_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM customers WHERE id = %s', (customer_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'address': row[4],
            'gst_number': row[5],
            'status': row[6]
        }
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'status': self.status
        }


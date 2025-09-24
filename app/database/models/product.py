from .base import get_db_connection

class Product:
    @staticmethod
    def create(data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO products (product_code, name, description, price, stock, status) VALUES (%s, %s, %s, %s, %s, %s)',
                (data['product_code'], data['name'], data['description'], data['price'], data['stock'], data['status'])
            )
            conn.commit()
            return Product.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM products')
            return [Product.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(product_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            row = cursor.fetchone()
            if row:
                return Product.from_row(row)
            return None

    @staticmethod
    def update(product_id, data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE products SET product_code = %s, name = %s, description = %s, price = %s, stock = %s, status = %s WHERE id = %s',
                (data['product_code'], data['name'], data['description'], data['price'], data['stock'], data['status'], product_id)
            )
            conn.commit()
            return Product.get_by_id(product_id)

    @staticmethod
    def delete(product_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        return {
            'id': row[0],
            'product_code': row[1],
            'name': row[2],
            'description': row[3],
            'price': row[4],
            'stock': row[5],
            'status': row[6]
        }
    def to_dict(self):
      return {
            'id': self.id,
            'product_code': self.product_code,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'status': self.status
      }

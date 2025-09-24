from ..db_manager import DBManager

class Product:
    @staticmethod
    def create(data):
        query = '''
        INSERT INTO products (product_code, name, description, price, stock, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        params = (data['product_code'], data['name'], data['description'], data['price'], data['stock'], data['status'])
        product_id = DBManager.execute_write_query(query, params)
        return Product.get_by_id(product_id)

    @staticmethod
    def get_all():
        query = 'SELECT * FROM products'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(product_id):
        query = 'SELECT * FROM products WHERE id = %s'
        return DBManager.execute_query(query, (product_id,), fetch='one')

    @staticmethod
    def update(product_id, data):
        query = '''
        UPDATE products 
        SET product_code = %s, name = %s, description = %s, price = %s, stock = %s, status = %s 
        WHERE id = %s
        '''
        params = (data['product_code'], data['name'], data['description'], data['price'], data['stock'], data['status'], product_id)
        DBManager.execute_write_query(query, params)
        return Product.get_by_id(product_id)

    @staticmethod
    def delete(product_id):
        query = 'DELETE FROM products WHERE id = %s'
        DBManager.execute_write_query(query, (product_id,))
        return {'message': 'Product deleted successfully'}

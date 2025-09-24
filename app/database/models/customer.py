from ..db_manager import DBManager

class Customer:
    @staticmethod
    def create(data):
        query = '''
        INSERT INTO customers (name, email, phone, address, gst_number, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        params = (data['name'], data['email'], data['phone'], data['address'], data['gst_number'], data['status'])
        customer_id = DBManager.execute_write_query(query, params)
        return Customer.get_by_id(customer_id)

    @staticmethod
    def get_all():
        query = 'SELECT * FROM customers'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(customer_id):
        query = 'SELECT * FROM customers WHERE id = %s'
        return DBManager.execute_query(query, (customer_id,), fetch='one')

    @staticmethod
    def update(customer_id, data):
        query = '''
        UPDATE customers 
        SET name = %s, email = %s, phone = %s, address = %s, gst_number = %s, status = %s 
        WHERE id = %s
        '''
        params = (data['name'], data['email'], data['phone'], data['address'], data['gst_number'], data['status'], customer_id)
        DBManager.execute_write_query(query, params)
        return Customer.get_by_id(customer_id)

    @staticmethod
    def delete(customer_id):
        query = 'DELETE FROM customers WHERE id = %s'
        # The execute_write_query returns the lastrowid, which is not what we want here.
        # We can create a more specific method in DBManager for deletes if needed,
        # but for now, we'll just return a success message.
        DBManager.execute_write_query(query, (customer_id,))
        # The number of affected rows is not easily available with the current abstraction
        return {'message': 'Customer deleted successfully'}

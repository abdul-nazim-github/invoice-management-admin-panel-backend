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
        # No need to fetch again, we can construct the object from the input data
        new_customer = data.copy()
        new_customer['id'] = customer_id
        return new_customer

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
        DBManager.execute_write_query(query, (customer_id,))
        return {'message': 'Customer deleted successfully'}

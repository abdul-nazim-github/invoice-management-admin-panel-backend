from ..db_manager import DBManager

class Payment:
    @staticmethod
    def create(data):
        query = '''
        INSERT INTO payments (invoice_id, payment_date, amount, payment_method, status)
        VALUES (%s, %s, %s, %s, %s)
        '''
        params = (data['invoice_id'], data['payment_date'], data['amount'], data['payment_method'], data['status'])
        payment_id = DBManager.execute_write_query(query, params)
        new_payment = data.copy()
        new_payment['id'] = payment_id
        return new_payment

    @staticmethod
    def get_all():
        query = 'SELECT * FROM payments'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(payment_id):
        query = 'SELECT * FROM payments WHERE id = %s'
        return DBManager.execute_query(query, (payment_id,), fetch='one')

    @staticmethod
    def update(payment_id, data):
        query = '''
        UPDATE payments 
        SET invoice_id = %s, payment_date = %s, amount = %s, payment_method = %s, status = %s 
        WHERE id = %s
        '''
        params = (data['invoice_id'], data['payment_date'], data['amount'], data['payment_method'], data['status'], payment_id)
        DBManager.execute_write_query(query, params)
        return Payment.get_by_id(payment_id)

    @staticmethod
    def delete(payment_id):
        query = 'DELETE FROM payments WHERE id = %s'
        DBManager.execute_write_query(query, (payment_id,))
        return {'message': 'Payment deleted successfully'}

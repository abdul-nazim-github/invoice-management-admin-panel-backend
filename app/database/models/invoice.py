from ..db_manager import DBManager

class Invoice:
    @staticmethod
    def create(data):
        query = '''
        INSERT INTO invoices (customer_id, invoice_date, total_amount, status)
        VALUES (%s, %s, %s, %s)
        '''
        params = (data['customer_id'], data['invoice_date'], data['total_amount'], data['status'])
        invoice_id = DBManager.execute_write_query(query, params)
        new_invoice = data.copy()
        new_invoice['id'] = invoice_id
        return new_invoice

    @staticmethod
    def get_all():
        query = 'SELECT * FROM invoices'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(invoice_id):
        query = 'SELECT * FROM invoices WHERE id = %s'
        return DBManager.execute_query(query, (invoice_id,), fetch='one')

    @staticmethod
    def update(invoice_id, data):
        query = '''
        UPDATE invoices 
        SET customer_id = %s, invoice_date = %s, total_amount = %s, status = %s 
        WHERE id = %s
        '''
        params = (data['customer_id'], data['invoice_date'], data['total_amount'], data['status'], invoice_id)
        DBManager.execute_write_query(query, params)
        return Invoice.get_by_id(invoice_id)

    @staticmethod
    def delete(invoice_id):
        query = 'DELETE FROM invoices WHERE id = %s'
        DBManager.execute_write_query(query, (invoice_id,))
        return {'message': 'Invoice deleted successfully'}

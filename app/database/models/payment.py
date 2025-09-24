"""
This module defines the Payment class, which encapsulates the logic for 
interacting with the payments table in the database.
"""

from ..db_manager import DBManager

class Payment:
    """
    Represents a payment in the system.
    This class contains static methods to perform CRUD operations on the payments table.
    """

    @staticmethod
    def create(data):
        """
        Creates a new payment in the database.

        Args:
            data (dict): A dictionary containing the payment's information.

        Returns:
            dict: A dictionary representing the newly created payment.
        """
        query = '''
        INSERT INTO payments (invoice_id, payment_date, amount, method, reference_no)
        VALUES (%s, %s, %s, %s, %s)
        '''
        params = (data['invoice_id'], data['payment_date'], data['amount'], data['method'], data.get('reference_no'))
        payment_id = DBManager.execute_write_query(query, params)
        new_payment = data.copy()
        new_payment['id'] = payment_id
        return new_payment

    @staticmethod
    def get_all():
        """
        Retrieves all payments from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a payment.
        """
        query = 'SELECT * FROM payments'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(payment_id):
        """
        Retrieves a single payment from the database by its ID.

        Args:
            payment_id (int): The ID of the payment to retrieve.

        Returns:
            dict: A dictionary representing the payment, or None if the payment is not found.
        """
        query = 'SELECT * FROM payments WHERE id = %s'
        return DBManager.execute_query(query, (payment_id,), fetch='one')

    @staticmethod
    def update(payment_id, data):
        """
        Updates an existing payment in the database.

        Args:
            payment_id (int): The ID of the payment to update.
            data (dict): A dictionary containing the payment's new information.

        Returns:
            dict: A dictionary representing the updated payment, or None if the payment is not found.
        """
        query = '''
        UPDATE payments 
        SET invoice_id = %s, payment_date = %s, amount = %s, method = %s, reference_no = %s 
        WHERE id = %s
        '''
        params = (data['invoice_id'], data['payment_date'], data['amount'], data['method'], data.get('reference_no'), payment_id)
        DBManager.execute_write_query(query, params)
        return Payment.get_by_id(payment_id)

    @staticmethod
    def delete(payment_id):
        """
        Deletes a payment from the database.

        Args:
            payment_id (int): The ID of the payment to delete.

        Returns:
            dict: A message confirming the deletion.
        """
        query = 'DELETE FROM payments WHERE id = %s'
        DBManager.execute_write_query(query, (payment_id,))
        return {'message': 'Payment deleted successfully'}

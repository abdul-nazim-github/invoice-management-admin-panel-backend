"""
This module defines the Invoice class, which encapsulates the logic for 
interacting with the invoices table in the database.
"""

from ..db_manager import DBManager

class Invoice:
    """
    Represents an invoice in the system.
    This class contains static methods to perform CRUD operations on the invoices table.
    """

    @staticmethod
    def create(data):
        """
        Creates a new invoice in the database.

        Args:
            data (dict): A dictionary containing the invoice's information.

        Returns:
            dict: A dictionary representing the newly created invoice.
        """
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
        """
        Retrieves all invoices from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents an invoice.
        """
        query = 'SELECT * FROM invoices'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(invoice_id):
        """
        Retrieves a single invoice from the database by its ID.

        Args:
            invoice_id (int): The ID of the invoice to retrieve.

        Returns:
            dict: A dictionary representing the invoice, or None if the invoice is not found.
        """
        query = 'SELECT * FROM invoices WHERE id = %s'
        return DBManager.execute_query(query, (invoice_id,), fetch='one')

    @staticmethod
    def update(invoice_id, data):
        """
        Updates an existing invoice in the database.

        Args:
            invoice_id (int): The ID of the invoice to update.
            data (dict): A dictionary containing the invoice's new information.

        Returns:
            dict: A dictionary representing the updated invoice, or None if the invoice is not found.
        """
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
        """
        Deletes an invoice from the database.

        Args:
            invoice_id (int): The ID of the invoice to delete.

        Returns:
            dict: A message confirming the deletion.
        """
        query = 'DELETE FROM invoices WHERE id = %s'
        DBManager.execute_write_query(query, (invoice_id,))
        return {'message': 'Invoice deleted successfully'}

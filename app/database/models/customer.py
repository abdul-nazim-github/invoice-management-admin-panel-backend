"""
This module defines the Customer class, which encapsulates the logic for 
interacting with the customers table in the database.
"""

from ..db_manager import DBManager

class Customer:
    """
    Represents a customer in the system.
    This class contains static methods to perform CRUD operations on the customers table.
    """

    @staticmethod
    def create(data):
        """
        Creates a new customer in the database.

        Args:
            data (dict): A dictionary containing the customer's information.

        Returns:
            dict: A dictionary representing the newly created customer.
        """
        query = '''
        INSERT INTO customers (name, email, phone, address, gst_number, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        params = (data['name'], data['email'], data['phone'], data['address'], data['gst_number'], data['status'])
        customer_id = DBManager.execute_write_query(query, params)
        new_customer = data.copy()
        new_customer['id'] = customer_id
        return new_customer

    @staticmethod
    def get_all():
        """
        Retrieves all customers from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a customer.
        """
        query = 'SELECT * FROM customers'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(customer_id):
        """
        Retrieves a single customer from the database by their ID.

        Args:
            customer_id (int): The ID of the customer to retrieve.

        Returns:
            dict: A dictionary representing the customer, or None if the customer is not found.
        """
        query = 'SELECT * FROM customers WHERE id = %s'
        return DBManager.execute_query(query, (customer_id,), fetch='one')

    @staticmethod
    def update(customer_id, data):
        """
        Updates an existing customer in the database.

        Args:
            customer_id (int): The ID of the customer to update.
            data (dict): A dictionary containing the customer's new information.

        Returns:
            dict: A dictionary representing the updated customer, or None if the customer is not found.
        """
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
        """
        Deletes a customer from the database.

        Args:
            customer_id (int): The ID of the customer to delete.

        Returns:
            dict: A message confirming the deletion.
        """
        query = 'DELETE FROM customers WHERE id = %s'
        DBManager.execute_write_query(query, (customer_id,))
        return {'message': 'Customer deleted successfully'}

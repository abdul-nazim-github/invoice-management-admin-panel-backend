"""
This module defines the Product class, which encapsulates the logic for 
interacting with the products table in the database.
"""

from ..db_manager import DBManager

class Product:
    """
    Represents a product in the system.
    This class contains static methods to perform CRUD operations on the products table.
    """

    @staticmethod
    def create(data):
        """
        Creates a new product in the database.

        Args:
            data (dict): A dictionary containing the product's information.

        Returns:
            dict: A dictionary representing the newly created product.
        """
        query = '''
        INSERT INTO products (product_code, name, description, price, stock, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        params = (data['product_code'], data['name'], data['description'], data['price'], data['stock'], data['status'])
        product_id = DBManager.execute_write_query(query, params)
        new_product = data.copy()
        new_product['id'] = product_id
        return new_product

    @staticmethod
    def get_all():
        """
        Retrieves all products from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a product.
        """
        query = 'SELECT * FROM products'
        return DBManager.execute_query(query, fetch='all')

    @staticmethod
    def get_by_id(product_id):
        """
        Retrieves a single product from the database by its ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            dict: A dictionary representing the product, or None if the product is not found.
        """
        query = 'SELECT * FROM products WHERE id = %s'
        return DBManager.execute_query(query, (product_id,), fetch='one')

    @staticmethod
    def update(product_id, data):
        """
        Updates an existing product in the database.

        Args:
            product_id (int): The ID of the product to update.
            data (dict): A dictionary containing the product's new information.

        Returns:
            dict: A dictionary representing the updated product, or None if the product is not found.
        """
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
        """
        Deletes a product from the database.

        Args:
            product_id (int): The ID of the product to delete.

        Returns:
            dict: A message confirming the deletion.
        """
        query = 'DELETE FROM products WHERE id = %s'
        DBManager.execute_write_query(query, (product_id,))
        return {'message': 'Product deleted successfully'}

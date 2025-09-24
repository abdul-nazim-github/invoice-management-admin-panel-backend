"""
This module defines the User class, which encapsulates the logic for 
interacting with the users table in the database.
"""

from .base import get_db_connection

class User:
    """
    Represents a user in the system.
    This class contains static methods to perform CRUD operations on the users table.
    """

    @staticmethod
    def create(data):
        """
        Creates a new user in the database.

        Args:
            data (dict): A dictionary containing the user's information (username, password, email).

        Returns:
            dict: A dictionary representing the newly created user, or None if creation fails.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                (data['username'], data['password'], data['email'])
            )
            conn.commit()
            return User.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        """
        Retrieves all users from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a user.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            return [User.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(user_id):
        """
        Retrieves a single user from the database by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            dict: A dictionary representing the user, or None if the user is not found.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            if row:
                return User.from_row(row)
            return None

    @staticmethod
    def update(user_id, data):
        """
        Updates an existing user in the database.

        Args:
            user_id (int): The ID of the user to update.
            data (dict): A dictionary containing the user's new information.

        Returns:
            dict: A dictionary representing the updated user, or None if the user is not found.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET username = %s, password = %s, email = %s WHERE id = %s',
                (data['username'], data['password'], data['email'], user_id)
            )
            conn.commit()
            return User.get_by_id(user_id)

    @staticmethod
    def delete(user_id):
        """
        Deletes a user from the database.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            bool: True if the user was successfully deleted, False otherwise.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        """
        Creates a user dictionary from a database row.

        Args:
            row (tuple): A tuple representing a row in the users table.

        Returns:
            dict: A dictionary representing the user.
        """
        return {
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'email': row[3]
        }

    def to_dict(self):
      """
      Converts a User object to a dictionary.

      Returns:
          dict: A dictionary representation of the user.
      """
      return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email
      }

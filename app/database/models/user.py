"""
This module defines the User class, which encapsulates the logic for 
interacting with the users table in the database.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from .base import get_db_connection

class User:
    """
    Represents a user in the system.
    This class is now a proper object model with instance methods.
    """
    def __init__(self, id, username, email, password_hash, role='staff', name=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.name = name

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Converts the User object to a dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'name': self.name
        }

    @classmethod
    def from_row(cls, row):
        """Creates a User object from a database row."""
        if not row:
            return None
        # Assuming row order is: id, username, email, password_hash, name, role
        return cls(id=row[0], username=row[1], email=row[2], password_hash=row[3], name=row[4], role=row[5])

    @staticmethod
def create(data):
    """
    Creates a new user in the database with a hashed password.
    """
    conn = get_db_connection()
    hashed_password = generate_password_hash(data['password'])
    role = data.get('role', 'staff')  # Default to 'staff' if no role is provided
    name = data.get('name')

    with conn.cursor() as cursor:
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, name, role) VALUES (%s, %s, %s, %s, %s)',
            (data['username'], data['email'], hashed_password, name, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return User.get_by_id(user_id)


    @classmethod
    def find_by_email(cls, email):
        """
        Retrieves a single user from the database by their email.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email, password_hash, name, role FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            return cls.from_row(row)

    @classmethod
    def get_by_id(cls, user_id):
        """
        Retrieodes a single user by their ID.
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email, password_hash, name, role FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return cls.from_row(row)
        
    @staticmethod
    def get_all():
        """
        Retrieves all users from the database.
        """
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT id, username, email, name, role FROM users')
            return cursor.fetchall()

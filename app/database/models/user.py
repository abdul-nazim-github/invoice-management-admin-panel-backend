from werkzeug.security import generate_password_hash, check_password_hash
from .base_model import BaseModel

class User(BaseModel):
    _table_name = 'users'

    def __init__(self, **kwargs):
        # Never store plain text password on the model instance
        if 'password' in kwargs:
            self.password_hash = self.hash_password(kwargs.pop('password'))
        super().__init__(**kwargs)

    # --- Password handling ---
    
    @staticmethod
    def hash_password(password):
        """Hashes a password for storing."""
        if not password:
            raise ValueError("Password cannot be empty.")
        return generate_password_hash(password)

    def check_password(self, password):
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # --- Custom Finder Methods ---

    @classmethod
    def find_by_username(cls, username, include_deleted=False):
        """Finds a user by their username."""
        db = cls._get_db_manager()
        row = db.find_one_where("username = %s", (username,), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        """Finds a user by their email address."""
        db = cls._get_db_manager()
        row = db.find_one_where("email = %s", (email,), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_username_or_email(cls, login_identifier, include_deleted=False):
        """Finds a user by either their username or email."""
        db = cls._get_db_manager()
        # Use a case-insensitive search for the identifier
        where_clause = "username ILIKE %s OR email ILIKE %s"
        params = (login_identifier, login_identifier)
        row = db.find_one_where(where_clause, params, include_deleted=include_deleted)
        return cls.from_row(row)

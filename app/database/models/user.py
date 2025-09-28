from werkzeug.security import generate_password_hash, check_password_hash
from .base_model import BaseModel

class User(BaseModel):
    _table_name = 'users'

    def __init__(self, **kwargs):
        # This constructor is used when creating instances from DB rows.
        # The password hash is already handled.
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
        if not hasattr(self, 'password_hash'):
            return False
        return check_password_hash(self.password_hash, password)

    # --- Overridden CRUD Methods ---

    @classmethod
    def create(cls, data):
        """
        Creates a new user, ensuring the password is hashed before saving.
        """
        if 'password' not in data:
            raise ValueError("Password is required to create a user.")

        # Hash the password and replace the plain-text one with the hash.
        hashed_password = cls.hash_password(data.pop('password'))
        data['password_hash'] = hashed_password
        
        # Now, call the generic create method from the base model with the corrected data.
        return super().create(data)

    # --- Custom Finder Methods ---

    @classmethod
    def find_by_username(cls, username, include_deleted=False):
        """Finds a user by their username."""
        db = cls._get_db_manager()
        row = db.find_one_where("LOWER(username) = %s", (username.lower(),), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        """Finds a user by their email address."""
        db = cls._get_db_manager()
        row = db.find_one_where("LOWER(email) = %s", (email.lower(),), include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def find_by_username_or_email(cls, login_identifier, include_deleted=False):
        """Finds a user by either their username or email using a case-insensitive search."""
        db = cls._get_db_manager()
        where_clause = "LOWER(username) = %s OR LOWER(email) = %s"
        params = (login_identifier.lower(), login_identifier.lower())
        row = db.find_one_where(where_clause, params, include_deleted=include_deleted)
        return cls.from_row(row)

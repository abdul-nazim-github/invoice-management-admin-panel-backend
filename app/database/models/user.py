from werkzeug.security import generate_password_hash, check_password_hash
from .base_model import BaseModel
from app.database.db_manager import DBManager

class User(BaseModel):
    _table_name = 'users'

    def __init__(self, id, username, email, password_hash, role='staff', name=None, **kwargs):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.name = name
        # Absorb any extra columns that might be in the database row
        for key, value in kwargs.items():
            setattr(self, key, value)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'name': self.name
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # Unpack the row dictionary into the constructor
        return cls(**row)

    @classmethod
    def create(cls, data):
        hashed_password = generate_password_hash(data['password'])
        role = data.get('role', 'staff')
        name = data.get('name')
        username = data['username']
        email = data['email']

        query = f'INSERT INTO {cls._table_name} (username, email, password_hash, name, role) VALUES (%s, %s, %s, %s, %s)'
        user_id = DBManager.execute_write_query(query, (username, email, hashed_password, name, role))
        
        # After creating, fetch the full user object
        return cls.find_by_id(user_id)

    @classmethod
    def find_by_email(cls, email, include_deleted=False):
        base_query = cls._get_base_query(include_deleted)
        # Use "AND" if the base query already has a "WHERE" clause (i.e., when not including deleted)
        # and "WHERE" if it doesn't.
        clause = "AND" if not include_deleted else "WHERE"
        query = f'{base_query} {clause} email = %s'
        result = DBManager.execute_query(query, (email,), fetch='one')
        return cls.from_row(result)

    @classmethod
    def find_by_username(cls, username, include_deleted=False):
        base_query = cls._get_base_query(include_deleted)
        # Use "AND" if the base query already has a "WHERE" clause (i.e., when not including deleted)
        # and "WHERE" if it doesn't.
        clause = "AND" if not include_deleted else "WHERE"
        query = f'{base_query} {clause} username = %s'
        result = DBManager.execute_query(query, (username,), fetch='one')
        return cls.from_row(result)

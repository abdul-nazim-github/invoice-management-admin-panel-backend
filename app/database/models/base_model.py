from app.database.db_manager import DBManager
from datetime import datetime, date
from decimal import Decimal
import json

# Helper for custom JSON serialization
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class BaseModel:
    """Base class for all models, providing common CRUD operations."""
    _table_name = None  # Must be defined in child classes
    _db_manager = None

    def __init__(self, **kwargs):
        # Assign all keyword arguments directly to attributes.
        # This keeps the original data types from the database (e.g., datetime objects).
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """
        Serializes the model instance to a dictionary, correctly handling
        special data types like datetimes and decimals for JSON conversion.
        """
        d = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        # Use json.dumps with the custom encoder and then json.loads to get a clean dict
        return json.loads(json.dumps(d, cls=CustomJsonEncoder))

    @classmethod
    def _get_db_manager(cls):
        """Returns a memoized instance of the DBManager for the model's table."""
        if cls._db_manager is None or cls._db_manager._table_name != cls._table_name:
            cls._db_manager = DBManager(cls._table_name)
        return cls._db_manager

    @classmethod
    def from_row(cls, row):
        """Creates a model instance from a database row dictionary."""
        if not row:
            return None
        return cls(**row)

    # --- Generic CRUD Methods ---

    @classmethod
    def create(cls, data):
        """
        Creates a new record. The model layer is responsible for
        the full create-then-fetch sequence.
        """
        db = cls._get_db_manager()
        table_columns = db.get_table_columns()
        sanitized_data = {key: data[key] for key in data if key in table_columns}
        
        if not sanitized_data:
            raise ValueError("No valid data provided for creation.")

        new_id = db.create(sanitized_data)
        
        if not new_id:
            return None

        return cls.find_by_id(new_id)

    @classmethod
    def find_by_id(cls, record_id, include_deleted=False):
        """Finds a record by its primary key."""
        db = cls._get_db_manager()
        row = db.get_by_id(record_id, include_deleted)
        return cls.from_row(row)

    @classmethod
    def get_all(cls, include_deleted=False):
        """Gets all records from the table."""
        db = cls._get_db_manager()
        rows = db.get_all(include_deleted)
        return [cls.from_row(row) for row in rows]

    @classmethod
    def update(cls, record_id, data):
        """
        Updates a record by its ID. The model layer is responsible
        for the full update-then-fetch sequence.
        """
        db = cls._get_db_manager()
        table_columns = db.get_table_columns()
        sanitized_data = {key: data[key] for key in data if key in table_columns and key != 'id'}

        if not sanitized_data:
            return cls.find_by_id(record_id)

        db.update(record_id, sanitized_data)
        return cls.find_by_id(record_id)

    @classmethod
    def delete(cls, record_id, soft_delete=True):
        """Deletes a record by its ID."""
        db = cls._get_db_manager()
        return db.delete(record_id, soft_delete)

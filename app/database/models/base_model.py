from app.database.db_manager import DBManager
from datetime import datetime, date
from decimal import Decimal

class BaseModel:
    """Base class for all models, providing common CRUD operations."""
    _table_name = None  # Must be defined in child classes
    _db_manager = None

    def __init__(self, **kwargs):
        # Dynamically set attributes for all columns in the kwargs
        for key, value in kwargs.items():
            setattr(self, key, self._format_value(key, value))

    def _format_value(self, key, value):
        """Helper to format values from the database correctly."""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

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

    # --- Generic CRUD Methods (Refactored) ---

    @classmethod
    def create(cls, data):
        """
        Creates a new record. The model layer is now responsible for
        the full create-then-fetch sequence.
        """
        db = cls._get_db_manager()
        table_columns = db.get_table_columns()
        sanitized_data = {key: data[key] for key in data if key in table_columns}
        
        if not sanitized_data:
            raise ValueError("No valid data provided for creation.")

        # Step 1: Create the record and get the new ID from the DBManager
        new_id = db.create(sanitized_data)
        
        if not new_id:
            return None

        # Step 2: Fetch the complete record using the standard find_by_id method
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
        Updates a record by its ID. The model layer is now responsible
        for the full update-then-fetch sequence.
        """
        db = cls._get_db_manager()
        table_columns = db.get_table_columns()
        sanitized_data = {key: data[key] for key in data if key in table_columns and key != 'id'}

        if not sanitized_data:
            return cls.find_by_id(record_id)

        # Step 1: Update the record. This method returns nothing.
        db.update(record_id, sanitized_data)

        # Step 2: Fetch the updated record using the standard find_by_id method
        return cls.find_by_id(record_id)

    @classmethod
    def delete(cls, record_id, soft_delete=True):
        """Deletes a record by its ID."""
        db = cls._get_db_manager()
        return db.delete(record_id, soft_delete)

from app.database.db_manager import DBManager
from datetime import datetime, date
from decimal import Decimal

class BaseModel:
    _db_manager = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__}({attrs})>"

    def to_dict(self):
        """Serializes the model instance to a dictionary, handling special types."""
        output = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            
            if isinstance(value, (datetime, date)):
                output[key] = value.isoformat()
            elif isinstance(value, Decimal):
                output[key] = str(value)
            else:
                output[key] = value
        return output

    @classmethod
    def _get_db_manager(cls):
        """Returns a DBManager instance for the model's table."""
        return DBManager(table_name=cls._table_name)

    @classmethod
    def from_row(cls, row):
        """Creates a model instance from a database row dictionary."""
        if not row:
            return None
        return cls(**row)

    @classmethod
    def find_by_id(cls, record_id, include_deleted=False):
        db = cls._get_db_manager()
        row = db.get_by_id(record_id, include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def create(cls, data):
        """Creates a new record and returns the full model instance."""
        db = cls._get_db_manager()
        record_id = db.create(data)
        # Fetch and return the newly created object, not just the ID
        return cls.find_by_id(record_id)

    @classmethod
    def update(cls, record_id, data):
        db = cls._get_db_manager()
        db.update(record_id, data)

    @classmethod
    def delete(cls, record_id, soft_delete=True):
        db = cls._get_db_manager()
        return db.delete(record_id, soft_delete=soft_delete)

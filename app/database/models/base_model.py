from app.database.db_manager import DBManager

class BaseModel:
    _table_name = None  # To be defined in child models (e.g., 'users')

    def __init__(self, **kwargs):
        """Generic constructor to create a model instance from a dictionary."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def _get_db_manager(cls):
        """Creates a DBManager instance for the current model's table."""
        if not cls._table_name:
            raise ValueError("Child model must set the '_table_name' attribute.")
        return DBManager(table_name=cls._table_name)

    @classmethod
    def from_row(cls, row_dict):
        """Creates a model instance from a database row dictionary."""
        if not row_dict:
            return None
        return cls(**row_dict)

    # --- Delegated CRUD & Search Operations ---

    @classmethod
    def create(cls, data):
        """Create a new record, returning a model instance."""
        db = cls._get_db_manager()
        new_row = db.create(data)
        return cls.from_row(new_row)

    @classmethod
    def find_all(cls, include_deleted=False):
        """Find all records, returning a list of model instances."""
        db = cls._get_db_manager()
        all_rows = db.get_all(include_deleted=include_deleted)
        return [cls.from_row(row) for row in all_rows]

    @classmethod
    def find_by_id(cls, record_id, include_deleted=False):
        """Find a single record by ID, returning a model instance."""
        db = cls._get_db_manager()
        row = db.get_by_id(record_id, include_deleted=include_deleted)
        return cls.from_row(row)

    @classmethod
    def update(cls, record_id, data):
        """Update a record, returning the updated model instance."""
        db = cls._get_db_manager()
        updated_row = db.update(record_id, data)
        return cls.from_row(updated_row)

    @classmethod
    def delete(cls, record_id, soft_delete=True):
        """Delete a record and return True on success."""
        db = cls._get_db_manager()
        return db.delete(record_id, soft_delete=soft_delete)

    @classmethod
    def find_with_pagination(cls, page=1, per_page=10, include_deleted=False):
        """Find records with pagination, returning instances and total count."""
        db = cls._get_db_manager()
        rows, total = db.get_paginated(page=page, per_page=per_page, include_deleted=include_deleted)
        items = [cls.from_row(row) for row in rows]
        return items, total

    @classmethod
    def search(cls, search_term, search_fields, include_deleted=False):
        """Search records, returning a list of model instances."""
        db = cls._get_db_manager()
        rows = db.search(search_term, search_fields, include_deleted=include_deleted)
        return [cls.from_row(row) for row in rows]

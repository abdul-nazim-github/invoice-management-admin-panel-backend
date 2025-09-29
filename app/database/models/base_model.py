
from app.database.db_manager import DBManager
from datetime import datetime

class BaseModel:
    _table_name = None

    def __init__(self, **kwargs):
        """
        Initializes the model instance by dynamically setting attributes for each
        key-value pair in kwargs. It specifically handles converting date/time
        strings for 'created_at' and 'updated_at' into datetime objects.
        """
        for key, value in kwargs.items():
            if key in ('created_at', 'updated_at', 'deleted_at') and isinstance(value, str):
                # Attempt to parse the string into a datetime object.
                # This handles cases where the DB driver returns strings.
                try:
                    value = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    # If parsing fails, leave it as is or log an error.
                    # For now, we proceed, but this indicates a data format issue.
                    pass
            setattr(self, key, value)

    @classmethod
    def _get_base_query(cls, include_deleted=False):
        if include_deleted:
            return f'SELECT * FROM {cls._table_name}'
        return f'SELECT * FROM {cls._table_name} WHERE deleted_at IS NULL'

    @classmethod
    def create(cls, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f'INSERT INTO {cls._table_name} ({columns}) VALUES ({placeholders})'
        return DBManager.execute_write_query(query, tuple(data.values()))

    @classmethod
    def find_all(cls, include_deleted=False):
        query = cls._get_base_query(include_deleted)
        results = DBManager.execute_query(query, fetch='all')
        return [cls.from_row(row) for row in results]

    @classmethod
    def find_by_id(cls, id, include_deleted=False):
        base_query = cls._get_base_query(include_deleted)
        clause = "AND" if "WHERE" in base_query else "WHERE"
        query = f'{base_query} {clause} id = %s'
        result = DBManager.execute_query(query, (id,), fetch='one')
        if result:
            return cls.from_row(result)
        return None

    @classmethod
    def update(cls, id, data):
        if not cls.find_by_id(id):
            return False
        
        if not data:
            return True

        set_clause_parts = [f"{key} = %s" for key in data.keys()]
        set_clause_parts.append("updated_at = NOW()")
        
        set_clause = ", ".join(set_clause_parts)
        
        query = f'UPDATE {cls._table_name} SET {set_clause} WHERE id = %s'
        
        params = list(data.values()) + [id]
        
        DBManager.execute_write_query(query, tuple(params))
        return True

    @classmethod
    def soft_delete(cls, id):
        if not cls.find_by_id(id):
            return False
        query = f'UPDATE {cls._table_name} SET deleted_at = NOW() WHERE id = %s'
        DBManager.execute_write_query(query, (id,))
        return True

    @classmethod
    def find_with_pagination_and_count(cls, page=1, per_page=10, include_deleted=False):
        offset = (page - 1) * per_page
        base_query = cls._get_base_query(include_deleted)
        
        query_data = f'{base_query} LIMIT %s OFFSET %s'
        results = DBManager.execute_query(query_data, (per_page, offset), fetch='all')
        items = [cls.from_row(row) for row in results]
        
        query_count = f'SELECT COUNT(*) as count FROM {cls._table_name}'
        if not include_deleted:
            query_count += ' WHERE deleted_at IS NULL'
        count_result = DBManager.execute_query(query_count, fetch='one')
        total = count_result['count']
        
        return items, total

    @classmethod
    def search(cls, search_term, search_fields, include_deleted=False):
        base_query = cls._get_base_query(include_deleted)
        clause = "AND" if "WHERE" in base_query else "WHERE"

        search_conditions = " OR ".join([f"{field} LIKE %s" for field in search_fields])
        query = f"{base_query} {clause} ({search_conditions})"

        search_pattern = f"%{search_term}%"
        params = [search_pattern] * len(search_fields)

        results = DBManager.execute_query(query, params, fetch='all')
        return [cls.from_row(row) for row in results]

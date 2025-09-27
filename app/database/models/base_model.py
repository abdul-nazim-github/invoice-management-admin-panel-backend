from app.database.db_manager import DBManager

class BaseModel:
    _table_name = None

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
        # Use "AND" if the base query already has a "WHERE" clause (i.e., when not including deleted)
        # and "WHERE" if it doesn't.
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
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f'UPDATE {cls._table_name} SET {set_clause} WHERE id = %s'
        DBManager.execute_write_query(query, (*data.values(), id))
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
        
        # Query for the data with pagination
        query_data = f'{base_query} LIMIT %s OFFSET %s'
        results = DBManager.execute_query(query_data, (per_page, offset), fetch='all')
        items = [cls.from_row(row) for row in results]
        
        # Query for the total count
        query_count = f'SELECT COUNT(*) as count FROM {cls._table_name}'
        if not include_deleted:
            query_count += ' WHERE deleted_at IS NULL'
        count_result = DBManager.execute_query(query_count, fetch='one')
        total = count_result['count']
        
        return items, total

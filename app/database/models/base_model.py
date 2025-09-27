from app.database.db_manager import DBManager

class BaseModel:
    _table_name = None

    @classmethod
    def _get_base_query(cls, include_deleted=False):
        if include_deleted:
            return f'SELECT * FROM {cls._table_name}'
        return f'SELECT * FROM {cls._table_name} WHERE is_deleted = FALSE'

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
        clause = "AND" if not include_deleted else "WHERE"
        query = f'{base_query} {clause} id = %s'
        result = DBManager.execute_query(query, (id,), fetch='one')
        return cls.from_row(result)

    @classmethod
    def update(cls, id, data):
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f'UPDATE {cls._table_name} SET {set_clause} WHERE id = %s'
        DBManager.execute_write_query(query, (*data.values(), id))

    @classmethod
    def soft_delete(cls, id):
        query = f'UPDATE {cls._table_name} SET is_deleted = TRUE, deleted_at = NOW() WHERE id = %s'
        DBManager.execute_write_query(query, (id,))

    @classmethod
    def find_with_pagination(cls, page=1, per_page=10, include_deleted=False):
        offset = (page - 1) * per_page
        base_query = cls._get_base_query(include_deleted)
        query = f'{base_query} LIMIT %s OFFSET %s'
        results = DBManager.execute_query(query, (per_page, offset), fetch='all')
        return [cls.from_row(row) for row in results]

    @classmethod
    def count(cls, include_deleted=False):
        query = f'SELECT COUNT(*) as count FROM {cls._table_name}'
        if not include_deleted:
            query += ' WHERE is_deleted = FALSE'
        result = DBManager.execute_query(query, fetch='one')
        return result['count']

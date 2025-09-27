from app.database.db_manager import DBManager
from datetime import datetime

class BaseModel:
    _table_name = ''

    @classmethod
    def _get_base_query(cls, include_deleted=False):
        query = f'SELECT * FROM {cls._table_name}'
        if not include_deleted:
            query += ' WHERE deleted_at IS NULL'
        return query

    @classmethod
    def find_all(cls, include_deleted=False):
        query = cls._get_base_query(include_deleted)
        return DBManager.execute_query(query, fetch='all')

    @classmethod
    def find_by_id(cls, _id, include_deleted=False):
        query = cls._get_base_query(include_deleted)
        query += f' AND id = %s' if not include_deleted else ' WHERE id = %s'
        return DBManager.execute_query(query, (_id,), fetch='one')

    @classmethod
    def soft_delete(cls, _id):
        query = f'UPDATE {cls._table_name} SET deleted_at = %s WHERE id = %s'
        return DBManager.execute_write_query(query, (datetime.utcnow(), _id))

    @classmethod
    def restore(cls, _id):
        query = f'UPDATE {cls._table_name} SET deleted_at = NULL WHERE id = %s'
        return DBManager.execute_write_query(query, (_id,))

    @classmethod
    def create(cls, data):
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        query = f'INSERT INTO {cls._table_name} ({keys}) VALUES ({values})'
        return DBManager.execute_write_query(query, tuple(data.values()))

    @classmethod
    def update(cls, _id, data):
        keys = ', '.join([f'{key} = %s' for key in data.keys()])
        query = f'UPDATE {cls._table_name} SET {keys} WHERE id = %s'
        return DBManager.execute_write_query(query, tuple(data.values()) + (_id,))

from .base import get_db_connection
from decimal import Decimal
from datetime import datetime, date

# --- Centralized Normalization Functions ---

def normalize_value(value):
    """Normalize values that the default JSON encoder can't handle."""
    if isinstance(value, Decimal):
        return float(value)
    return value

def normalize_row(row):
    """Normalize all values in a DB row dictionary."""
    if not row:
        return None
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize a list of DB row dictionaries."""
    return [normalize_row(r) for r in rows]

# --- DBManager Class ---

class DBManager:
    """A class to simplify and centralize database interactions."""

    def __init__(self, table_name=None):
        self._table_name = table_name

    def get_table_columns(self):
        if not self._table_name:
            raise ValueError("DBManager must have a table_name for this operation.")
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self._table_name} LIMIT 0")
                return [desc[0] for desc in cursor.description]
        finally:
            conn.close()
            
    # --- Generic Raw SQL Execution ---

    def fetch_one_raw(self, query, params=None):
        """Executes a raw SQL query and returns a single, normalized row."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                return normalize_row(row)
        finally:
            conn.close()

    def fetch_all_raw(self, query, params=None):
        """Executes a raw SQL query and returns all normalized rows."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return normalize_rows(rows)
        finally:
            conn.close()

    # --- Read Operations (Table-specific) ---

    def get_all(self, include_deleted=False):
        query = f"SELECT * FROM {self._table_name}"
        if not include_deleted and 'is_deleted' in self.get_table_columns():
            query += " WHERE is_deleted = FALSE"
        query += " ORDER BY created_at DESC"
        return self.fetch_all_raw(query)

    def get_by_id(self, record_id, include_deleted=False):
        query = f"SELECT * FROM {self._table_name} WHERE id = %s"
        params = [record_id]
        if not include_deleted and 'is_deleted' in self.get_table_columns():
            query += " AND is_deleted = FALSE"
        return self.fetch_one_raw(query, tuple(params))

    def find_one_where(self, where_clause, params, include_deleted=False):
        query = f"SELECT * FROM {self._table_name} WHERE {where_clause}"
        final_params = list(params)
        if not include_deleted and 'is_deleted' in self.get_table_columns():
            query += " AND is_deleted = FALSE"
        return self.fetch_one_raw(query, tuple(final_params))

    def get_paginated(self, page=1, per_page=10, include_deleted=False):
        offset = (page - 1) * per_page
        
        count_query = f"SELECT COUNT(*) as total FROM {self._table_name}"
        if not include_deleted and 'is_deleted' in self.get_table_columns():
            count_query += " WHERE is_deleted = FALSE"
        total_result = self.fetch_one_raw(count_query)
        total = total_result['total'] if total_result else 0

        data_query = f"SELECT * FROM {self._table_name}"
        if not include_deleted and 'is_deleted' in self.get_table_columns():
            data_query += " WHERE is_deleted = FALSE"
        data_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        rows = self.fetch_all_raw(data_query, (per_page, offset))
        
        return rows, total
            
    # --- Write Operations ---

    def create(self, data):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {self._table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, tuple(data.values()))
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update(self, record_id, data):
        if not data:
            return
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            set_clause_parts = [f"{key} = %s" for key in data.keys()]
            if 'updated_at' in self.get_table_columns() and 'updated_at' not in data:
                set_clause_parts.append("updated_at = NOW()")
            set_clause = ", ".join(set_clause_parts)
            query = f"UPDATE {self._table_name} SET {set_clause} WHERE id = %s"
            params = list(data.values()) + [record_id]
            cursor.execute(query, tuple(params))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self, record_id, soft_delete=True):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if soft_delete and 'is_deleted' in self.get_table_columns():
                query = f"UPDATE {self._table_name} SET is_deleted = TRUE, deleted_at = NOW() WHERE id = %s"
            else:
                query = f"DELETE FROM {self._table_name} WHERE id = %s"
            cursor.execute(query, (record_id,))
            rowcount = cursor.rowcount
            conn.commit()
            return rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def restore(self, record_id):
        """Restores a soft-deleted record. Returns True on success."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if 'is_deleted' in self.get_table_columns():
                query = f"UPDATE {self._table_name} SET is_deleted = FALSE, deleted_at = NULL WHERE id = %s"
                cursor.execute(query, (record_id,))
                rowcount = cursor.rowcount
                conn.commit()
                return rowcount > 0
            return False # Table doesn't support soft delete
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

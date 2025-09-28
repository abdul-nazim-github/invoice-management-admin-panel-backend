from .base import get_db_connection
from decimal import Decimal
from datetime import datetime, date

# --- Centralized Normalization Functions ---

def normalize_value(value):
    """Normalize values that the default JSON encoder can't handle."""
    if isinstance(value, Decimal):
        return float(value)
    # Datetime objects are handled by the serialization schema (Marshmallow)
    return value

def normalize_row(row):
    """Normalize all values in a DB row dictionary."""
    if not row:
        return None
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize a list of DB row dictionaries."""
    return [normalize_row(r) for r in rows]

# --- DBManager Class (Refactored for Separation of Concerns) ---

class DBManager:
    """A class to simplify and centralize database interactions."""

    def __init__(self, table_name):
        self._table_name = table_name

    def get_table_columns(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self._table_name} LIMIT 0")
                return [desc[0] for desc in cursor.description]
        finally:
            conn.close()

    # --- Read Operations ---

    def get_all(self, include_deleted=False):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = f"SELECT * FROM {self._table_name}"
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    query += " WHERE is_deleted = FALSE"
                query += " ORDER BY created_at DESC"
                cursor.execute(query)
                rows = cursor.fetchall()
                return normalize_rows(rows)
        finally:
            conn.close()

    def get_by_id(self, record_id, include_deleted=False):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = f"SELECT * FROM {self._table_name} WHERE id = %s"
                params = [record_id]
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    query += " AND is_deleted = FALSE"
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()
                return normalize_row(row)
        finally:
            conn.close()

    def find_one_where(self, where_clause, params, include_deleted=False):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = f"SELECT * FROM {self._table_name} WHERE {where_clause}"
                final_params = list(params)
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    query += " AND is_deleted = FALSE"
                cursor.execute(query, tuple(final_params))
                row = cursor.fetchone()
                return normalize_row(row)
        finally:
            conn.close()

    def search(self, search_term, search_fields, include_deleted=False):
        if not search_fields:
            return []
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                where_clauses = [f"LOWER({field}) LIKE %s" for field in search_fields]
                query = f"SELECT * FROM {self._table_name} WHERE {' OR '.join(where_clauses)}"
                params = [f"%{search_term.lower()}%"] * len(search_fields)
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    query += " AND is_deleted = FALSE"
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                return normalize_rows(rows)
        finally:
            conn.close()

    def get_paginated(self, page=1, per_page=10, include_deleted=False):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                offset = (page - 1) * per_page
                count_query = f"SELECT COUNT(*) as total FROM {self._table_name}"
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    count_query += " WHERE is_deleted = FALSE"
                cursor.execute(count_query)
                total = cursor.fetchone()['total']
                data_query = f"SELECT * FROM {self._table_name}"
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    data_query += " WHERE is_deleted = FALSE"
                data_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                cursor.execute(data_query, (per_page, offset))
                rows = cursor.fetchall()
                return normalize_rows(rows), total
        finally:
            conn.close()
            
    # --- Write Operations (Focused on a single task) ---

    def create(self, data):
        """Executes an INSERT statement and returns the new record's ID."""
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
        """Executes an UPDATE statement. Returns nothing."""
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
        """Executes a DELETE or soft-delete UPDATE. Returns True on success."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if soft_delete and 'is_deleted' in self.get_table_columns():
                query = f"UPDATE {self._table_name} SET is_deleted = TRUE, updated_at = NOW() WHERE id = %s"
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

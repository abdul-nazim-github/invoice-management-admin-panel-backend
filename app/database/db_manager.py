from .base import get_db_connection
from decimal import Decimal
from datetime import datetime, date

# --- Centralized Normalization Functions ---

def normalize_value(value):
    """Recursively normalize values for JSON serialization."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

def normalize_row(row):
    """Normalize all values in a DB row dictionary."""
    if not row:
        return None
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize a list of DB row dictionaries."""
    return [normalize_row(r) for r in rows]

# --- DBManager Class (Definitive Fix) ---

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

    # --- Read Operations (No changes needed here) ---

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
                if not include_deleted and 'is_deleted' in self.get_table_columns():
                    query += " AND is_deleted = FALSE"
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()
                return normalize_row(row)
        finally:
            conn.close()
            
    # Other read operations (get_all, search, etc.) are omitted for brevity
    # but remain unchanged.

    # --- Write Operations (Corrected with simple, robust transaction pattern) ---

    def create(self, data):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {self._table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, tuple(data.values()))
            new_id = cursor.lastrowid
            conn.commit()  # The transaction is now saved.
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        # After the transaction is committed and connection closed, fetch the new record.
        return self.get_by_id(new_id)

    def update(self, record_id, data):
        if not data:
            return self.get_by_id(record_id)
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
            conn.commit() # The transaction is now saved.
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        # After the transaction, fetch the updated record.
        return self.get_by_id(record_id)

    def delete(self, record_id, soft_delete=True):
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

from .base import get_db_connection
from decimal import Decimal
from datetime import datetime, date

# --- Centralized Normalization Functions ---

def normalize_value(value):
    """Recursively normalize values for JSON serialization."""
    if isinstance(value, Decimal):
        # Convert Decimal to float for JSON numbers
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

def normalize_row(row):
    """Normalize all values in a DB row dictionary."""
    # Assumes row is a dictionary, as provided by DictCursor
    if not row:
        return None
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize a list of DB row dictionaries."""
    return [normalize_row(r) for r in rows]

# --- DBManager Class ---

class DBManager:
    """A class to simplify database interactions."""

    def __init__(self, table_name, model_class):
        self._table_name = table_name
        self._model_class = model_class

    def get_all(self, include_deleted=False):
        """Fetches all records from the table."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM {self._table_name}"
            if not include_deleted and 'is_deleted' in self.get_table_columns():
                query += " WHERE is_deleted = FALSE"
            cursor.execute(query)
            rows = cursor.fetchall()
            return normalize_rows(rows)
        finally:
            conn.close()

    def get_by_id(self, record_id, include_deleted=False):
        """Fetches a single record by its ID."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM {self._table_name} WHERE id = %s"
            params = [record_id]
            if not include_deleted and 'is_deleted' in self.get_table_columns():
                query += " AND is_deleted = FALSE"
            
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return normalize_row(row) if row else None
        finally:
            conn.close()

    def search(self, search_term, search_fields, include_deleted=False):
        """Searches for records where search_term matches any of the search_fields."""
        if not search_fields:
            return []

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Using ILIKE for case-insensitive search
            where_clauses = [f"{field} ILIKE %s" for field in search_fields]
            query = f"SELECT * FROM {self._table_name} WHERE {' OR '.join(where_clauses)}"
            params = [f"%{search_term}%"] * len(search_fields)

            if not include_deleted and 'is_deleted' in self.get_table_columns():
                query += " AND is_deleted = FALSE"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return normalize_rows(rows)
        finally:
            conn.close()

    def get_table_columns(self):
        """Helper to get column names for the table."""
        # This is a simplified implementation. In a real app, you might cache this.
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self._table_name} LIMIT 0")
            return [desc[0] for desc in cursor.description]
        finally:
            conn.close()


from .base import get_db_connection
from decimal import Decimal
from datetime import datetime, date

# --- Centralized Normalization Functions ---

def normalize_value(value):
    """Recursively normalize values for JSON serialization."""
    if isinstance(value, Decimal):
        # Return string to preserve formatting (e.g., "33333.00")
        return "{:.2f}".format(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

def normalize_row(row):
    """Normalize all values in a DB row dictionary."""
    # Assumes row is a dictionary, as provided by DictCursor
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize a list of DB row dictionaries."""
    return [normalize_row(r) for r in rows]

# --- DBManager Class ---

class DBManager:
    """
    A centralized manager for handling all database interactions.
    This class abstracts away connection/cursor handling and normalizes output data.
    """

    @staticmethod
    def execute_query(query, params=None, fetch=None):
        """
        Executes a read-only query and returns normalized data.
        This method relies on pymysql.cursors.DictCursor being set for the
        connection, which returns each row as a dictionary.
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())

                if fetch == 'one':
                    # fetchone() with DictCursor returns a single dictionary or None
                    row = cursor.fetchone()
                    return normalize_row(row) if row else None

                if fetch == 'all':
                    # fetchall() with DictCursor returns a list of dictionaries
                    rows = cursor.fetchall()
                    return normalize_rows(rows) if rows else []

            return None
        finally:
            conn.close()

    @staticmethod
    def execute_write_query(query, params=None):
        """
        Executes a write query (INSERT, UPDATE, DELETE) and commits the transaction.
        Returns the ID of the last inserted row.
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                last_id = cursor.lastrowid
            conn.commit()
            return last_id
        finally:
            conn.close()


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
    """Normalize all values in a DB row (dictionary)."""
    if not row:
        return {}
    # Assumes row is a dictionary
    return {k: normalize_value(v) for k, v in row.items()}

def normalize_rows(rows):
    """Normalize multiple DB rows."""
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
        """
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())

            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]

            if fetch == 'one':
                row = cursor.fetchone()
                if not row:
                    return None
                # Create a dictionary and normalize it
                dict_row = dict(zip(columns, row))
                return normalize_row(dict_row)

            if fetch == 'all':
                rows = cursor.fetchall()
                if not rows:
                    return []
                # Create a list of dictionaries and normalize them
                dict_rows = [dict(zip(columns, r)) for r in rows]
                return normalize_rows(dict_rows)

        return None

    @staticmethod
    def execute_write_query(query, params=None):
        """
        Executes a write query (INSERT, UPDATE, DELETE) and commits the transaction.
        Returns the ID of the last inserted row.
        """
        conn = get_db_connection()
        last_id = None
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            last_id = cursor.lastrowid
        conn.commit()
        return last_id

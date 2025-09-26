# =============================
# app/database/models/user_model.py
# =============================
import logging
from typing import Any, Dict, Optional
from app.utils.response import normalize_row
from app.database.base import get_db_connection

def create_user(
    username: str,
    email: str,
    password_hash: str,
    name: str = '',
    role: str = "admin",
    twofa_secret: str = '',
    billing_address: str = '',
    billing_city: str = '',
    billing_state: str = '',
    billing_pin: str = '',
    billing_gst: str = '',
) -> Optional[Dict[str, Any]]:
    """Creates a new user and returns their data."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    username, email, password_hash, name, role, twofa_secret,
                    billing_address, billing_city, billing_state, billing_pin, billing_gst
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username, email, password_hash, name, role, twofa_secret,
                    billing_address, billing_city, billing_state, billing_pin, billing_gst,
                ),
            )
            new_user_id = cur.lastrowid
        conn.commit()
        return find_user_by_id(new_user_id)
    finally:
        conn.close()

def find_user(identifier: str) -> Optional[Dict[str, Any]]:
    """Finds a user by their email or username."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE email=%s OR username=%s LIMIT 1",
                (identifier, identifier)
            )
            return normalize_row(cur.fetchone())
    finally:
        conn.close()

def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Finds a user by their ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return normalize_row(cur.fetchone())
    finally:
        conn.close()

def update_user_profile(user_id: int, **fields) -> Optional[Dict[str, Any]]:
    """Dynamically updates a user's profile fields."""
    if not fields:
        return find_user_by_id(user_id)

    # Build dynamic SET clause
    set_clause = ", ".join([f"{key} = %s" for key in fields])
    params = list(fields.values())
    params.append(user_id)

    sql = f"UPDATE users SET {set_clause} WHERE id = %s"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows_affected = cur.execute(sql, tuple(params))
        conn.commit()
        if rows_affected > 0:
            return find_user_by_id(user_id)
        return None # User not found or not updated
    except Exception as e:
        logging.error(f"Error updating user profile: {e}")
        return None
    finally:
        conn.close()

def update_user_password(user_id: int, new_hash: str) -> bool:
    """Updates a user's password hash."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows_affected = cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (new_hash, user_id),
            )
        conn.commit()
        return rows_affected > 0
    finally:
        conn.close()

def update_user_billing(user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Updates user billing details using COALESCE to only update provided fields.
    Maps Python-style kwargs to database column names.
    """
    # Map kwargs to DB columns
    db_mapping = {
        "address": "billing_address",
        "city": "billing_city",
        "state": "billing_state",
        "pin": "billing_pin",
        "gst": "billing_gst",
    }
    
    update_fields = {db_mapping[k]: v for k, v in kwargs.items() if k in db_mapping}

    if not update_fields:
        return find_user_by_id(user_id)

    set_clause = ", ".join([f"{col} = %s" for col in update_fields])
    params = list(update_fields.values())
    params.append(user_id)

    sql = f"UPDATE users SET {set_clause} WHERE id = %s"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows_affected = cur.execute(sql, tuple(params))
        conn.commit()
        if rows_affected > 0:
            return find_user_by_id(user_id)
        return None
    finally:
        conn.close()

"""
This module handles authentication-related database operations, including token blacklisting 
and removal of expired tokens.
"""

from uuid6 import uuid7
from app.database.base import get_db_connection
import time
import jwt
from flask import current_app

def blacklist_token(user_id: str, token: str) -> bool:
    """
    Adds a user's token to the blacklist to invalidate it.

    Args:
        user_id (str): The ID of the user.
        token (str): The JWT token to be blacklisted.

    Returns:
        bool: True if the token was successfully blacklisted, False otherwise.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO token_blacklist (id, user_id, token) VALUES (%s, %s, %s)",
                (str(uuid7()), user_id, token)
            )
        conn.commit()
        return True
    finally:
        conn.close()

def is_token_blacklisted(token: str) -> bool:
    """
    Checks if a given token is present in the blacklist.

    Args:
        token (str): The JWT token to check.

    Returns:
        bool: True if the token is blacklisted, False otherwise.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM token_blacklist WHERE token=%s LIMIT 1", (token,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def remove_expired_tokens():
    """
    Removes expired tokens from the blacklist to keep it clean and efficient.

    Returns:
        int: The number of expired tokens that were removed.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, token FROM token_blacklist")
            rows = cur.fetchall()
            expired_ids = []

            for row in rows:
                token_id = row["id"]
                token = row["token"]
                try:
                    payload = jwt.decode(
                        token,
                        current_app.config["JWT_SECRET"],
                        algorithms=["HS256"],
                        options={"verify_exp": False}
                    )
                    if payload.get("exp", 0) < int(time.time()):
                        expired_ids.append(token_id)
                except Exception:
                    expired_ids.append(token_id)

            if expired_ids:
                cur.execute(
                    "DELETE FROM token_blacklist WHERE id IN (%s)" %
                    ",".join(["%s"]*len(expired_ids)),
                    expired_ids
                )
                conn.commit()
            return len(expired_ids)
    finally:
        conn.close()

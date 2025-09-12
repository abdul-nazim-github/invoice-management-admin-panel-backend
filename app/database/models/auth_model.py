from uuid6 import uuid7
from app.database.base import get_db_connection
import time
import jwt
from flask import current_app

def blacklist_token(user_id: str, token: str) -> bool:
    """Add token to blacklist"""
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
    """Check if token is blacklisted"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM token_blacklist WHERE token=%s LIMIT 1", (token,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def remove_expired_tokens():
    """Remove expired tokens from blacklist"""
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

# =============================
# app/database/models/user_model.py
# =============================
from typing import Any, Dict
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_user(
    username: str,
    email: str,
    password_hash: str,
    full_name: str = '',
    role: str = "admin",
    twofa_secret: str = '',
    billing_address: str = '',
    billing_city: str = '',
    billing_state: str = '',
    billing_pin: str = '',
    billing_gst: str = '',
) -> str:
    conn = get_db_connection()
    try:
        user_id = str(uuid7())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    id, username, email, password_hash, full_name, role, twofa_secret,
                    billing_address, billing_city, billing_state, billing_pin, billing_gst
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user_id,
                    username,
                    email,
                    password_hash,
                    full_name,
                    role,
                    twofa_secret,
                    billing_address,
                    billing_city,
                    billing_state,
                    billing_pin,
                    billing_gst,
                ),
            )
        conn.commit()
        return user_id
    finally:
        conn.close()


def find_user(identifier: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE email=%s OR username=%s LIMIT 1",
                (identifier, identifier)
            )
            return cur.fetchone()
    finally:
        conn.close()

def find_user_by_id(user_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_user_profile(user_id: str, full_name: str = '', email: str = '') -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users 
                SET full_name=COALESCE(%s, full_name), 
                    email=COALESCE(%s, email) 
                WHERE id=%s
                """,
                (full_name, email, user_id),
            )
        conn.commit()
        return find_user_by_id(user_id)
    finally:
        conn.close()


def update_user_password(user_id: str, new_hash: str) -> bool:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (new_hash, user_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def update_user_2fa(user_id: str, secret: str) -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET twofa_secret=%s WHERE id=%s",
                (secret, user_id),
            )
        conn.commit()
        return find_user_by_id(user_id)
    finally:
        conn.close()


def update_user_billing(
    user_id: str,
    address: str = '',
    city: str = '',
    state: str = '',
    pin: str = '',
    gst: str = '',
) -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users 
                SET billing_address=COALESCE(%s, billing_address), 
                    billing_city=COALESCE(%s, billing_city), 
                    billing_state=COALESCE(%s, billing_state), 
                    billing_pin=COALESCE(%s, billing_pin), 
                    billing_gst=COALESCE(%s, billing_gst)
                WHERE id=%s
                """,
                (address, city, state, pin, gst, user_id),
            )
        conn.commit()
        return find_user_by_id(user_id)
    finally:
        conn.close()

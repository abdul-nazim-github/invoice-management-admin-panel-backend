# =============================
# app/database/models/user_model.py
# =============================
from uuid6 import uuid7
from app.database.base import get_db_connection


def create_user(
    username,
    email,
    password_hash,
    name=None,
    role="admin",
    twofa_secret=None,
    bill_address=None,
    bill_city=None,
    bill_state=None,
    bill_pin=None,
    bill_gst=None,
):
    try:
        conn = get_db_connection()
        user_id = str(uuid7())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, username, email, password_hash, name, role, twofa_secret,
                                   bill_address, bill_city, bill_state, bill_pin, bill_gst)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user_id,
                    username,
                    email,
                    password_hash,
                    name,
                    role,
                    twofa_secret,
                    bill_address,
                    bill_city,
                    bill_state,
                    bill_pin,
                    bill_gst,
                ),
            )
        conn.commit()
        return user_id
    finally:
        conn.close()


def find_user_by_email(email):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email))
            return cur.fetchone()
    finally:
        conn.close()


def find_user_by_id(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_user_profile(user_id, name=None, email=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET name=COALESCE(%s,name), email=COALESCE(%s,email) WHERE id=%s",
                (name, email, user_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def update_user_password(user_id, new_hash):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id)
            )
        conn.commit()
        return True
    finally:
        conn.close()


def update_user_2fa(user_id, secret):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET twofa_secret=%s WHERE id=%s", (secret, user_id)
            )
        conn.commit()
        return True
    finally:
        conn.close()


def update_user_billing(user_id, addr=None, city=None, state=None, pin=None, gst=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users 
                   SET bill_address=%s, bill_city=%s, bill_state=%s, bill_pin=%s, bill_gst=%s
                   WHERE id=%s""",
                (addr, city, state, pin, gst, user_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()

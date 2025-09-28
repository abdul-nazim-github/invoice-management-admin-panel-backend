from datetime import datetime
import hashlib
import random
import re
import string

from app.database.base import get_db_connection


def short_customer_code(customer_id: str, length: int = 4) -> str:
    """Generate a short customer code from UUID"""
    # Take first 'length' characters of md5 hash of the UUID
    customer_id_str = str(customer_id)
    hash_val = hashlib.md5(customer_id_str.encode()).hexdigest()
    return hash_val[:length].upper()


def generate_invoice_number(conn, customer_id: str) -> str:
    ym = datetime.now().strftime("%Y%m")
    cust_code = short_customer_code(customer_id)

    with conn.cursor() as cur:
        # Get the maximum sequence globally
        cur.execute(
            """
            SELECT MAX(CAST(SUBSTRING_INDEX(invoice_number, '-', -1) AS UNSIGNED)) AS max_seq
            FROM invoices
            WHERE invoice_number REGEXP 'INV-[0-9]{6}-[A-Z0-9]+-[0-9]{3}'
            """
        )
        result = cur.fetchone()
        max_seq = result["max_seq"] or 0  # 0 if no invoices found
        seq = max_seq + 1

    seq_str = str(seq).zfill(3)
    return f"INV-{ym}-{cust_code}-{seq_str}"

def generate_unique_product_code(product_name):
    conn = get_db_connection()
    try:
        while True:
            # Generate Product Code
            clean_name = re.sub(r'[^A-Za-z0-9 ]', '', product_name).strip()
            words = clean_name.split()
            prefix = "".join(word[0].upper() for word in words[:3])
            if len(prefix) < 3 and words:
                prefix += (words[0][1:4-len(prefix)].upper())
            if len(prefix) < 3:
                prefix += "X" * (3 - len(prefix))
            rand_num = ''.join(random.choices(string.digits, k=4))
            product_code = f"{prefix}-{rand_num}"

            # Check uniqueness
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM products WHERE product_code=%s", (product_code,))
                if not cur.fetchone():
                    return product_code
    finally:
        conn.close()
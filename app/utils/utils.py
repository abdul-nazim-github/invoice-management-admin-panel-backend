from datetime import datetime
import hashlib


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

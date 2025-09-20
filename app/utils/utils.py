from datetime import datetime
import hashlib


def short_customer_code(customer_id: str, length: int = 4) -> str:
    """Generate a short customer code from UUID"""
    # Take first 'length' characters of md5 hash of the UUID
    customer_id_str = str(customer_id)
    hash_val = hashlib.md5(customer_id_str.encode()).hexdigest()
    return hash_val[:length].upper()

def generate_invoice_number(conn, customer_id: str) -> str:
    """Generate a unique invoice number like INV-YYYYMM-CUST-SEQ"""
    # Year + month
    ym = datetime.now().strftime("%Y%m")
    
    # Short customer code
    cust_code = short_customer_code(customer_id)
    # Default sequence
    seq = 1
    with conn.cursor() as cur:
        # Use tuple access safely
        cur.execute(
            """
            SELECT invoice_number FROM invoices
            WHERE invoice_number LIKE %s
            ORDER BY invoice_number DESC
            LIMIT 1
            """,
            (f"INV-{ym}-{cust_code}-%",)
        )
        last = cur.fetchone()
        if last:
            # If using tuple, get first element
            last_invoice = last[0]  # or last['invoice_number'] if dict cursor
            try:
                last_seq = int(last_invoice.split("-")[-1])
                seq = last_seq + 1
            except Exception:
                seq = 1  # fallback

    # Format sequence as 3 digits
    seq_str = str(seq).zfill(3)

    invoice_number = f"INV-{ym}-{cust_code}-{seq_str}"
    return invoice_number

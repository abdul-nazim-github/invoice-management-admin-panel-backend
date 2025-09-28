import re
from datetime import datetime

def is_valid_date(date_string):
    """Validates that a string is in 'YYYY-MM-DD' format."""
    if not date_string or not isinstance(date_string, str):
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def is_valid_status(status, allowed_statuses):
    """Validates that a status is in a list of allowed statuses."""
    return status in allowed_statuses

def is_valid_name(name):
    """
    Validates that the name contains only alphabetic characters and spaces.
    - Must not be empty.
    - Can contain multiple space-separated names, hyphens, and apostrophes.
    """
    if not name or not isinstance(name, str):
        return False
    # Allows for names like "John Doe", "Mary-Anne", "O'Connell"
    pattern = r"^[a-zA-Z' -]+$"
    return re.match(pattern, name) is not None

def is_valid_gst_number(gst_number):
    """
    Validates the Indian GST Identification Number format.
    Format: 2-digit state code, 10-digit PAN, 1-digit entity code, 'Z', 1-digit checksum.
    Example: 29ABCDE1234F1Z5
    """
    if not gst_number or not isinstance(gst_number, str):
        return False
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return re.match(pattern, gst_number) is not None

def is_valid_email(email):
    """
    Performs a basic validation of an email address format.
    """
    if not email or not isinstance(email, str):
        return False
    # A widely used regex for email validation
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """
    Validates that a phone number contains only digits, optionally with a leading '+'.
    Must be between 10 and 15 digits long.
    """
    if not phone or not isinstance(phone, str):
        return False
    pattern = r"^\+?[0-9]{10,15}$"
    return re.match(pattern, phone) is not None

def is_valid_product_code(code):
    """Validates that the product code is alphanumeric and between 3 to 20 characters."""
    if not code or not isinstance(code, str):
        return False
    pattern = r"^[a-zA-Z0-9-]{3,20}$"
    return re.match(pattern, code) is not None

def is_valid_price(price):
    """Validates that the price is a positive number (integer or float)."""
    return isinstance(price, (int, float)) and price > 0

def is_valid_stock(stock):
    """Validates that the stock is a non-negative integer."""
    return isinstance(stock, int) and stock >= 0

def validate_customer_data(data, is_update=False):
    """
    Validates customer data for create and update operations.
    Returns a list of error messages. An empty list means the data is valid.
    """
    errors = []
    
    if not is_update:
        required_fields = ['name', 'email', 'phone', 'address', 'gst_number']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return errors

    if 'name' in data and not is_valid_name(data['name']):
        errors.append("Invalid name. Only letters, spaces, hyphens, and apostrophes are allowed.")
        
    if 'email' in data and not is_valid_email(data['email']):
        errors.append("Invalid email address format.")
        
    if 'phone' in data and not is_valid_phone(data['phone']):
        errors.append("Invalid phone number format. Must be 10-15 digits, optionally starting with a '+'.")

    if 'gst_number' in data and not is_valid_gst_number(data['gst_number']):
        errors.append("Invalid GST number format. The format should be like '29ABCDE1234F1Z5'.")

    return errors

def validate_product_data(data, is_update=False):
    """Validates product data for create and update operations."""
    errors = []

    if not is_update:
        required_fields = ['product_code', 'name', 'description', 'price', 'stock']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return errors

    if 'product_code' in data and not is_valid_product_code(data['product_code']):
        errors.append("Invalid product code. Must be 3-20 alphanumeric characters or hyphens.")

    if 'name' in data and (not isinstance(data['name'], str) or len(data['name']) < 3):
        errors.append("Product name must be a string of at least 3 characters.")

    if 'price' in data and not is_valid_price(data['price']):
        errors.append("Invalid price. Must be a positive number.")

    if 'stock' in data and not is_valid_stock(data['stock']):
        errors.append("Invalid stock. Must be a non-negative integer.")

    return errors

def validate_invoice_data(data, is_update=False):
    """Validates invoice data for create and update operations."""
    errors = []

    if not is_update:
        required_fields = ['customer_id', 'invoice_date', 'due_date', 'items']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return errors

    if 'customer_id' in data and (not isinstance(data['customer_id'], int) or data['customer_id'] <= 0):
        errors.append("customer_id must be a positive integer.")

    if 'invoice_date' in data and not is_valid_date(data['invoice_date']):
        errors.append("Invalid invoice_date format. Use YYYY-MM-DD.")

    if 'due_date' in data and not is_valid_date(data['due_date']):
        errors.append("Invalid due_date format. Use YYYY-MM-DD.")

    if 'status' in data and not is_valid_status(data['status'], ['pending', 'paid', 'cancelled']):
        errors.append("Invalid status. Must be one of: pending, paid, cancelled.")

    if 'items' in data:
        if not isinstance(data['items'], list) or not data['items']:
            errors.append("'items' must be a non-empty list.")
        else:
            for i, item in enumerate(data['items']):
                if not isinstance(item, dict):
                    errors.append(f"Item at index {i} is not a valid object.")
                    continue
                item_errors = []
                if 'product_id' not in item or not isinstance(item['product_id'], int) or item['product_id'] <= 0:
                    item_errors.append("product_id must be a positive integer.")
                if 'quantity' not in item or not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                    item_errors.append("quantity must be a positive integer.")
                if item_errors:
                    errors.append(f"Validation failed for item at index {i}: {', '.join(item_errors)}")
    return errors

def validate_payment_data(data, is_update=False):
    """Validates payment data for create and update operations."""
    errors = []
    
    if not is_update:
        required_fields = ['invoice_id', 'amount', 'payment_date', 'method']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return errors

    if 'invoice_id' in data and (not isinstance(data['invoice_id'], int) or data['invoice_id'] <= 0):
        errors.append("invoice_id must be a positive integer.")

    if 'amount' in data and not is_valid_price(data['amount']):
        errors.append("Invalid amount. Must be a positive number.")

    if 'payment_date' in data and not is_valid_date(data['payment_date']):
        errors.append("Invalid payment_date format. Use YYYY-MM-DD.")

    if 'method' in data and (not isinstance(data['method'], str) or len(data['method']) < 3):
        errors.append("Invalid payment method. Must be a string of at least 3 characters.")

    if 'reference_no' in data and (not isinstance(data['reference_no'], str) or len(data['reference_no']) < 5):
        errors.append("Invalid reference number. Must be a string of at least 5 characters.")

    return errors

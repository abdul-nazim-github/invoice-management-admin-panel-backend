def create_product_schema():
    with open('app/database/schemas/product_schema.sql', 'r') as f:
        return f.read()

def create_customer_schema():
    with open('app/database/schemas/customer_schema.sql', 'r') as f:
        return f.read()

def create_invoice_schema():
    with open('app/database/schemas/invoice_schema.sql', 'r') as f:
        return f.read()

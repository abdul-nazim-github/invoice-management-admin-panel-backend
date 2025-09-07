from .base import get_db_connection


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
        id CHAR(36) PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(100),
        role ENUM('admin','user') DEFAULT 'user',
        bill_address TEXT,
        bill_city VARCHAR(100),
        bill_state VARCHAR(100),
        bill_pin VARCHAR(20),
        bill_gst VARCHAR(50),
        twofa_secret VARCHAR(32) DEFAULT NULL,   -- ✅ added here
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # CUSTOMERS table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS customers (
        id CHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        phone VARCHAR(20),
        address TEXT,
        gst_number VARCHAR(50),
        status ENUM('active','inactive') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # PRODUCTS table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS products (
        id CHAR(36) PRIMARY KEY,
        product_code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        stock INT DEFAULT 0,
        status ENUM('active','inactive') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    )

    # INVOICES table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS invoices (
        id CHAR(36) PRIMARY KEY,
        invoice_number VARCHAR(50) UNIQUE NOT NULL,
        customer_id CHAR(36) NOT NULL,
        tax_percent DECIMAL(5,2) DEFAULT 0,
        discount DECIMAL(10,2) DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL,
        status ENUM('pending','paid','partial') DEFAULT 'pending',
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );
    """
    )

    # INVOICE_ITEMS table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS invoice_items (
        id CHAR(36) PRIMARY KEY,
        invoice_id CHAR(36) NOT NULL,
        product_id CHAR(36) NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10,2) NOT NULL DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """
    )

    # PAYMENTS table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS payments (
        id CHAR(36) PRIMARY KEY,
        invoice_id CHAR(36) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        method ENUM('cash','card','upi','bank') DEFAULT 'cash',
        reference_no VARCHAR(100),
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    );
    """
    )

    conn.commit()
    conn.close()

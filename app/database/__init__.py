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
            full_name VARCHAR(100),
            phone VARCHAR(20),
            role ENUM('admin','user') DEFAULT 'user',
            billing_address TEXT,
            billing_city VARCHAR(100),
            billing_state VARCHAR(100),
            billing_pin VARCHAR(20),
            billing_gst VARCHAR(50),
            twofa_secret VARCHAR(32) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL
        );
        """
    )

    # CUSTOMERS table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id CHAR(36) PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(20),
            address TEXT,
            gst_number VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL
        );
        """
    )

    # PRODUCTS table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id CHAR(36) PRIMARY KEY,
            sku VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            unit_price DECIMAL(10,2) NOT NULL,
            stock_quantity INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL
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
            tax_amount DECIMAL(10,2) NOT NULL,
            discount_amount DECIMAL(10,2) DEFAULT 0,
            subtotal_amount DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status ENUM('Pending','Paid','Overdue') DEFAULT 'Pending',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL,
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
            unit_price DECIMAL(10,2) NOT NULL DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL,
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
            reference_number VARCHAR(100),
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );
        """
    )

    # TOKEN_BLACKLIST table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS token_blacklist (
            id CHAR(36) PRIMARY KEY,
            user_id CHAR(36) NOT NULL,
            token VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()

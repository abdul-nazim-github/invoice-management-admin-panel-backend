-- ==================================================================
--                      DATABASE SCHEMA
-- ==================================================================
-- This script defines the database schema for the application.
-- It creates all the necessary tables, columns, relationships, and indexes.
-- ==================================================================

-- ------------------------------------------------------------------
-- Table: users
-- Purpose: Stores user accounts, credentials, and profile information.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL, -- User's unique login name
  email VARCHAR(255) UNIQUE NOT NULL,    -- User's unique email address
  password_hash VARCHAR(255) NOT NULL,   -- Hashed password for security
  name VARCHAR(255),                     -- User's full name
  role ENUM('admin','staff','manager') DEFAULT 'staff', -- User's role for access control
  twofa_secret VARCHAR(64),              -- Secret key for two-factor authentication
  billing_address TEXT,                     -- Billing address details
  billing_city VARCHAR(120),
  billing_state VARCHAR(120),
  billing_pin VARCHAR(20),
  billing_gst VARCHAR(50),                  -- User's GST number for billing
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of user creation
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- Indexes for faster queries
  INDEX idx_users_email (email),
  INDEX idx_users_username (username),
  INDEX idx_users_name (name),
  INDEX idx_users_role (role)
);

-- ------------------------------------------------------------------
-- Table: customers
-- Purpose: Stores information about the customers.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,              -- Customer's name
  email VARCHAR(255),                      -- Customer's email address
  phone VARCHAR(20),                       -- Customer's phone number
  address TEXT,                            -- Customer's physical address
  gst_number VARCHAR(50),                  -- Customer's GST identification number
  status ENUM('active','inactive') DEFAULT 'active', -- Customer's status
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of customer creation

  -- Indexes for faster queries
  INDEX idx_customers_full_name (full_name),
  INDEX idx_customers_email (email),
  INDEX idx_customers_phone (phone),
  INDEX idx_customers_gst_number (gst_number),
  INDEX idx_customers_status (status)
);

-- ------------------------------------------------------------------
-- Table: products
-- Purpose: Stores details of all products or services offered.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_code VARCHAR(50) UNIQUE NOT NULL,-- Unique code for product identification
  name VARCHAR(255) NOT NULL,              -- Name of the product
  description TEXT,                        -- Detailed description of the product
  price DECIMAL(10,2) NOT NULL,            -- Price of the product
  stock INT DEFAULT 0,                     -- Current stock level
  status ENUM('active','inactive') DEFAULT 'active', -- Product availability status
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of product creation

  -- Indexes for faster queries
  INDEX idx_products_code_name (product_code, name),
  INDEX idx_products_name (name),
  INDEX idx_products_status (status),
  INDEX idx_products_price (price),
  INDEX idx_products_stock (stock)
);

-- ------------------------------------------------------------------
-- Table: invoices
-- Purpose: Stores the main details of each invoice (header).
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  invoice_number VARCHAR(50) UNIQUE NOT NULL, -- Unique number for the invoice
  customer_id INT NOT NULL,                -- Foreign key linking to the customer
  user_id INT NOT NULL,                    -- Foreign key linking to the user who created the invoice
  invoice_date DATE NOT NULL,              -- Date the invoice was issued
  due_date DATE,                           -- Date the payment is due
  total_amount DECIMAL(10,2) NOT NULL,     -- The final amount of the invoice
  status ENUM('Paid','Pending','Overdue') DEFAULT 'Pending', -- Current status of the invoice
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of invoice creation

  -- Foreign key constraints
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,

  -- Indexes for faster queries
  INDEX idx_invoices_status_date (status, invoice_date),
  INDEX idx_invoices_customer_id (customer_id),
  INDEX idx_invoices_user_id (user_id),
  INDEX idx_invoices_due_date (due_date),
  INDEX idx_invoices_total_amount (total_amount)
);

-- ------------------------------------------------------------------
-- Table: invoice_items
-- Purpose: Stores individual line items for each invoice.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoice_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  invoice_id INT NOT NULL,                 -- Foreign key linking to the invoice
  product_id INT NOT NULL,                 -- Foreign key linking to the product
  quantity INT NOT NULL,                   -- Quantity of the product sold
  price DECIMAL(10,2) NOT NULL,            -- Price per unit at the time of sale
  total DECIMAL(10,2) NOT NULL,            -- Total amount for this line item (quantity * price)

  -- Foreign key constraints
  FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,

  -- Indexes for faster queries
  INDEX idx_invoice_items_invoice (invoice_id),
  INDEX idx_invoice_items_product_id (product_id)
);

-- ------------------------------------------------------------------
-- Table: payments
-- Purpose: Records all payments made against invoices.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  invoice_id INT NOT NULL,                 -- Foreign key linking to the invoice being paid
  amount DECIMAL(10,2) NOT NULL,           -- The amount that was paid
  payment_date DATE NOT NULL,              -- The date the payment was made
  method ENUM('cash','card','upi','bank_transfer') DEFAULT 'cash', -- Method of payment
  reference_no VARCHAR(100),               -- A reference number from the payment processor
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of payment record creation

  -- Foreign key constraints
  FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,

  -- Indexes for faster queries
  INDEX idx_payments_invoice (invoice_id),
  INDEX idx_payments_payment_date (payment_date),
  INDEX idx_payments_method (method),
  INDEX idx_payments_reference_no (reference_no)
);

-- ------------------------------------------------------------------
-- Table: token_blacklist
-- Purpose: Stores blacklisted JWT tokens to handle logouts.
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS token_blacklist (
  id VARCHAR(36) PRIMARY KEY,                -- Unique identifier for the blacklisted token
  user_id INT NOT NULL,                      -- The user associated with the token
  token VARCHAR(512) NOT NULL,               -- The blacklisted JWT token
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the token was blacklisted

  -- Foreign key constraint
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

  -- Indexes for faster queries
  INDEX idx_token_blacklist_token (token)
);

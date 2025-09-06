CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    method ENUM('cash','card','upi','bank_transfer') DEFAULT 'cash',
    reference_no VARCHAR(100), -- transaction id / cheque no etc.
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

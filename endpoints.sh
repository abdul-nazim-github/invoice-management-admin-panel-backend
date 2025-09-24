#!/bin/bash

BASE_URL="http://localhost:5001/api"
TOKEN=""
ADMIN_TOKEN=""

# Health Check
echo "Health Check"
curl -X GET $BASE_URL/health
echo "\n"

# -----------------
# Auth Endpoints
# -----------------

echo "Login as Admin"
# This will return a token that you can use for admin requests
ADMIN_TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{
  "email": "admin@example.com",
  "password": "adminpassword"
}' $BASE_URL/auth/login | jq -r .access_token)
echo "Admin Token: $ADMIN_TOKEN"
echo "\n"

echo "Register User (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "Test User"
}' $BASE_URL/users/register
echo "\n"

echo "Login as User"
# This will return a token that you can use for authenticated requests
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{
  "email": "test@example.com",
  "password": "password123"
}' $BASE_URL/auth/login | jq -r .access_token)
echo "User Token: $TOKEN"
echo "\n"

echo "Forgot Password"
curl -X POST -H "Content-Type: application/json" -d '{
  "email": "test@example.com"
}' $BASE_URL/auth/forgot
echo "\n"

echo "Reset Password"
# You will get a token from the forgot password email
RESET_TOKEN="your_reset_token"
curl -X POST -H "Content-Type: application/json" -d '{
  "token": "'$RESET_TOKEN'",
  "new_password": "newpassword123"
}' $BASE_URL/auth/reset
echo "\n"

echo "Enable 2FA"
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE_URL/auth/enable-2fa
echo "\n"

# -----------------
# Users Endpoints
# -----------------

echo "Get current user"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/users/me
echo "\n"

echo "Update user profile"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
  "full_name": "Test User Updated"
}' $BASE_URL/users/profile
echo "\n"

echo "Update password"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
  "old_password": "password123",
  "new_password": "newpassword456"
}' $BASE_URL/users/password
echo "\n"

# -----------------
# Dashboard Endpoint
# -----------------

echo "Dashboard"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/dashboard
echo "\n"

# -----------------
# Customers Endpoints
# -----------------

echo "Create customer (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "full_name": "New Customer",
    "email": "customer@example.com",
    "phone": "1234567890",
    "address": "456 Customer Ave",
    "gst_number": "GSTIN67890"
}' $BASE_URL/customers/
echo "\n"

echo "Get all customers"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/customers/
echo "\n"

echo "Get customer by ID"
CUSTOMER_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/customers/$CUSTOMER_ID
echo "\n"

echo "Update customer (as Admin)"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "full_name": "Updated Customer Name"
}' $BASE_URL/customers/$CUSTOMER_ID
echo "\n"

echo "Bulk delete customers (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/customers/bulk-delete
echo "\n"

# -----------------
# Products Endpoints
# -----------------

echo "Create product (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "name": "New Product",
    "description": "A shiny new product",
    "unit_price": 19.99,
    "stock_quantity": 100
}' $BASE_URL/products/
echo "\n"

echo "Get all products"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/products/
echo "\n"

echo "Get product by ID"
PRODUCT_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/products/$PRODUCT_ID
echo "\n"

echo "Update product (as Admin)"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "unit_price": 24.99
}' $BASE_URL/products/$PRODUCT_ID
echo "\n"

echo "Bulk delete products (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/products/bulk-delete
echo "\n"

# -----------------
# Invoices Endpoints
# -----------------

echo "Create invoice (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "customer_id": 1,
    "due_date": "2024-12-31",
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 2, "quantity": 1}
    ]
}' $BASE_URL/invoices/
echo "\n"

echo "Get all invoices"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/invoices/
echo "\n"

echo "Get invoice detail"
INVOICE_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/invoices/$INVOICE_ID
echo "\n"

echo "Update invoice (as Admin)"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "status": "Paid"
}' $BASE_URL/invoices/$INVOICE_ID
echo "\n"

echo "Pay invoice (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "amount": 100.00,
    "method": "card",
    "reference_no": "12345"
}' $BASE_URL/invoices/$INVOICE_ID/pay
echo "\n"

echo "Bulk delete invoices (as Admin)"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ADMIN_TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/invoices/bulk-delete
echo "\n"

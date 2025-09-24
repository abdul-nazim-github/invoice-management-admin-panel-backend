#!/bin/bash

BASE_URL="http://localhost:5001/api"
TOKEN=""

# Health Check
echo "Health Check"
curl -X GET $BASE_URL/health
echo "\n"

# -----------------
# Auth Endpoints
# -----------------

echo "Register"
curl -X POST -H "Content-Type: application/json" -d '{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}' $BASE_URL/auth/register
echo "\n"

echo "Login"
# This will return a token that you can use for authenticated requests
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{
  "email": "test@example.com",
  "password": "password123"
}' $BASE_URL/auth/login | jq -r .access_token)
echo "Token: $TOKEN"
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
  "name": "Test User",
  "bill_address": "123 Test St",
  "bill_city": "Testville",
  "bill_state": "Testland",
  "bill_pin": "12345",
  "bill_gst": "GSTIN12345"
}' $BASE_URL/users/profile
echo "\n"

echo "Update password"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
  "current_password": "password123",
  "new_password": "newpassword456"
}' $BASE_URL/users/password
echo "\n"

echo "Get billing info"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/users/billing
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

echo "Create customer"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "name": "New Customer",
    "email": "customer@example.com",
    "phone": "1234567890",
    "address": "456 Customer Ave",
    "gst_number": "GSTIN67890",
    "status": "active"
}' $BASE_URL/customers
echo "\n"

echo "Get all customers"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/customers
echo "\n"

echo "Get customer by ID"
CUSTOMER_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/customers/$CUSTOMER_ID
echo "\n"

echo "Update customer"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "name": "Updated Customer Name"
}' $BASE_URL/customers/$CUSTOMER_ID
echo "\n"

echo "Delete customer"
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE_URL/customers/$CUSTOMER_ID
echo "\n"

echo "Bulk delete customers"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/customers/bulk-delete
echo "\n"

# -----------------
# Products Endpoints
# -----------------

echo "Create product"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "product_code": "PROD001",
    "name": "New Product",
    "description": "A shiny new product",
    "price": 19.99,
    "stock": 100,
    "status": "active"
}' $BASE_URL/products
echo "\n"

echo "Get all products"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/products
echo "\n"

echo "Get product by ID"
PRODUCT_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/products/$PRODUCT_ID
echo "\n"

echo "Update product"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "price": 24.99
}' $BASE_URL/products/$PRODUCT_ID
echo "\n"

echo "Delete product"
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE_URL/products/$PRODUCT_ID
echo "\n"

echo "Bulk delete products"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/products/bulk-delete
echo "\n"

# -----------------
# Invoices Endpoints
# -----------------

echo "Create invoice"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "customer_id": 1,
    "due_date": "2024-12-31",
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 2, "quantity": 1, "price": 25.00}
    ]
}' $BASE_URL/invoices
echo "\n"

echo "Get all invoices"
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/invoices
echo "\n"

echo "Get invoice detail"
INVOICE_ID=1
curl -X GET -H "Authorization: Bearer $TOKEN" $BASE_URL/invoices/$INVOICE_ID
echo "\n"

echo "Update invoice"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "status": "Paid"
}' $BASE_URL/invoices/$INVOICE_ID
echo "\n"

echo "Pay invoice"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "amount": 100.00,
    "method": "card"
}' $BASE_URL/invoices/$INVOICE_ID/pay
echo "\n"

echo "Bulk delete invoices"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{
    "ids": [1, 2, 3]
}' $BASE_URL/invoices/bulk-delete
echo "\n"

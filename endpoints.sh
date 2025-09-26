#!/bin/bash

# ==============================================================================
#                 API Endpoint cURL Commands
# ==============================================================================
#
# INSTRUCTIONS:
#
# 1. Find the endpoint you want to test.
# 2. Copy the entire curl command.
# 3. Paste it into your terminal or import it into Postman.
# 4. **IMPORTANT**: Replace placeholder values (e.g., YOUR_ADMIN_TOKEN_HERE, 
#    YOUR_USER_TOKEN_HERE, and ID numbers like 1, 2, 3) with actual values.
#
# ==============================================================================

BASE_URL="http://localhost:5001/api"

# -----------------
# Health Check
# -----------------
echo "### Health Check ###"
curl -X GET $BASE_URL/health


# -----------------
# Auth Endpoints
# -----------------
echo "\n### Login as Admin (to get Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -d '{
  "email": "admin@example.com",
  "password": "adminpassword"
}' $BASE_URL/auth/login


echo "\n### Register a New User (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "name": "Test User"
}' $BASE_URL/auth/register


echo "\n### Login as Standard User (to get User Token) ###"
curl -X POST -H "Content-Type: application/json" -d '{
  "email": "test@example.com",
  "password": "password123"
}' $BASE_URL/auth/login


# -----------------
# Users Endpoints
# -----------------
echo "\n### Get Current User Profile (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/users/me


# -----------------
# Customers Endpoints
# -----------------
echo "\n### Create a New Customer (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "full_name": "New Customer",
    "email": "customer@example.com",
    "phone": "1234567890",
    "address": "456 Customer Ave",
    "gst_number": "GSTIN67890"
}' $BASE_URL/customers/


echo "\n### Get All Customers (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/customers/


echo "\n### Get Customer by ID (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/customers/1


echo "\n### Update a Customer (Requires Admin Token) ###"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "full_name": "Updated Customer Name"
}' $BASE_URL/customers/1


echo "\n### Bulk Delete Customers (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' $BASE_URL/customers/bulk-delete


# -----------------
# Products Endpoints
# -----------------
echo "\n### Create a New Product (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "product_code": "PROD-001",
    "name": "New Product",
    "description": "A shiny new product",
    "price": 19.99,
    "stock": 100
}' $BASE_URL/products/


echo "\n### Get All Products (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/products/


echo "\n### Get Product by ID (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/products/1


echo "\n### Update a Product (Requires Admin Token) ###"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "price": 24.99
}' $BASE_URL/products/1


echo "\n### Bulk Delete Products (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' $BASE_URL/products/bulk-delete


# -----------------
# Invoices Endpoints
# -----------------
echo "\n### Create a New Invoice (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "customer_id": 1,
    "invoice_date": "2024-08-15",
    "due_date": "2024-09-15",
    "items": [
        {"product_id": 1, "quantity": 2}
    ]
}' $BASE_URL/invoices/


echo "\n### Get All Invoices (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/invoices/


echo "\n### Get Invoice by ID (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" $BASE_URL/invoices/1


echo "\n### Update an Invoice (Requires Admin Token) ###"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "status": "Paid"
}' $BASE_URL/invoices/1


echo "\n### Pay an Invoice (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "amount": 100.00,
    "method": "card",
    "reference_no": "PAY-12345"
}' $BASE_URL/invoices/1/pay


echo "\n### Bulk Delete Invoices (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' $BASE_URL/invoices/bulk-delete


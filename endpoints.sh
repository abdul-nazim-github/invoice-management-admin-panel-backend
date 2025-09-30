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
curl -X GET "$BASE_URL/health/"


# -----------------
# Auth Endpoints
# -----------------
echo "\n### Sign In as Admin (to get Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -d '{
  "email": "admin@example.com",
  "password": "adminpassword"
}' "$BASE_URL/auth/sign-in/"


echo "\n### Register a New User (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "name": "Test User"
}' "$BASE_URL/auth/register/"


echo "\n### Sign In as Standard User (to get User Token) ###"
curl -X POST -H "Content-Type: application/json" -d '{
  "email": "test@example.com",
  "password": "password123"
}' "$BASE_URL/auth/sign-in/"


echo "\n### Sign Out (Requires Any Valid Token) ###"
curl -X POST -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/auth/sign-out/"


# -----------------
# Users Endpoints
# -----------------
echo "\n### Get Current User Profile (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/users/me/"


# -----------------
# Customers Endpoints
# -----------------
echo "\n### Create a New Customer (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "name": "New Customer",
    "email": "customer@example.com",
    "phone": "1234567890",
    "address": "456 Customer Ave",
    "gst_number": "GSTIN67890"
}' "$BASE_URL/customers/"


echo "\n### Get All Customers (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/customers/"


echo "\n### Get Customer by ID (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/customers/1/"


echo "\n### Update a Customer (Requires Admin Token) ###"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "name": "Updated Customer Name"
}' "$BASE_URL/customers/1/"


echo "\n### Bulk Delete Customers (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' "$BASE_URL/customers/bulk-delete/"


# -----------------
# Products Endpoints
# -----------------
echo "\n### Create a New Product (Requires Admin Token) ###"
# NOTE: The 'price' field handles decimals correctly (e.g., 24.30).
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "name": "Precision Screwdriver",
    "description": "A high-quality precision screwdriver for delicate tasks.",
    "price": 24.30,
    "stock": 150
}' "$BASE_URL/products/"


echo "\n### Get All Products (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/products/"


echo "\n### Get Product by ID (Requires User Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/products/1/"


echo "\n### Update a Product (Requires Admin Token) ###"
# NOTE: The 'price' field handles decimals correctly (e.g., 25.50).
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "price": 25.50
}' "$BASE_URL/products/1/"


echo "\n### Bulk Delete Products (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' "$BASE_URL/products/bulk-delete/"


# -----------------
# Invoices Endpoints
# -----------------
echo "\n### Create a New Invoice (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "customer_id": 1,
    "due_date": "2024-09-15",
    "items": [
        {"product_id": 1, "quantity": 3}
    ],
    "status": "Pending"
}' "$BASE_URL/invoices/"


echo "\n### Create a New Invoice with Precision Discount and Tax (Requires Admin Token) ###"
# NOTE: 'discount_amount' and 'tax_percent' now handle precision correctly (e.g., 5.50, 8.20).
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "customer_id": 1,
    "due_date": "2024-09-20",
    "items": [
        {"product_id": 1, "quantity": 2}
    ],
    "discount_amount": 5.50,
    "tax_percent": 8.20,
    "status": "Pending"
}' "$BASE_URL/invoices/"


echo "\n### Get All Invoices (Requires User Token) ###"
# NOTE: The response now includes the 'amount_paid' for each invoice.
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/invoices/"


echo "\n### Get Invoice by ID (Requires User Token) ###"
# NOTE: The response now includes the calculated 'amount_paid'.
curl -X GET -H "Authorization: Bearer YOUR_USER_TOKEN_HERE" "$BASE_URL/invoices/1/"


echo "\n### Update an Invoice (Requires Admin Token) ###"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "status": "Paid"
}' "$BASE_URL/invoices/1/"


echo "\n### Pay an Invoice (Requires Admin Token) ###"
# NOTE: To test this, first 'Get Invoice by ID' to see the current 'amount_paid', 
# then run this command, and then 'Get Invoice by ID' again to see the updated 'amount_paid'.
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "amount": 100.00,
    "method": "card",
    "reference_no": "PAY-12345"
}' "$BASE_URL/invoices/1/pay/"


echo "\n### Bulk Delete Invoices (Requires Admin Token) ###"
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" -d '{
    "ids": [1, 2]
}' "$BASE_URL/invoices/bulk-delete/"

# -----------------
# Dashboard Endpoints
# -----------------
echo "\n### Get Dashboard Stats (Requires Admin Token) ###"
curl -X GET -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" "$BASE_URL/dashboard/stats/"

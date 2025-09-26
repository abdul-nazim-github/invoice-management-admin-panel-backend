#!/bin/bash

# ==============================================================================
#                 API Endpoint Test Script
# ==============================================================================
#
# INSTRUCTIONS:
#
# 1. Make sure your Flask application is running.
# 2. Make sure you have `jq` installed to format JSON output (`brew install jq` or `apt-get install jq`).
# 3. Run this script from your terminal: `./endpoints.sh`
#
# ==============================================================================

# --- Configuration ---
BASE_URL="http://localhost:5001/api"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="adminpassword"
USER_EMAIL="testuser@example.com"
USER_PASSWORD="password123"

# --- Helper function for printing headers ---
print_header() {
    echo ""
    echo "=============================================================================="
    echo "  $1"
    echo "=============================================================================="
    echo ""
}

# --- Initial Health Check ---
print_header "Running Health Check"
curl -X GET $BASE_URL/health | jq .
echo ""


# ==============================================================================
#                       ADMIN FLOW
# ==============================================================================

# --- Admin Login ---
print_header "Attempting to log in as Admin to get Admin Token"
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "email": "'$ADMIN_EMAIL'",
        "password": "'$ADMIN_PASSWORD'"
      }' \
  $BASE_URL/auth/login)

ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | jq -r .access_token)

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "Failed to get Admin Token. The server responded with:"
    echo $ADMIN_LOGIN_RESPONSE | jq .
    echo "Exiting."
    exit 1
fi

echo "Successfully retrieved Admin Token."
echo ""


# --- Register a New User (as Admin) ---
print_header "Registering a new Standard User (as Admin)"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
        "username": "testuser",
        "email": "'$USER_EMAIL'",
        "password": "'$USER_PASSWORD'",
        "name": "Test User"
      }' \
  $BASE_URL/users/register | jq .


# --- Create a Customer (as Admin) and Capture ID ---
print_header "Creating a new Customer (as Admin)"
NEW_CUSTOMER_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
        "full_name": "Dynamic Test Customer",
        "email": "dynamic.customer@example.com",
        "phone": "9876543210",
        "address": "123 Dynamic Ave",
        "gst_number": "GSTIN-DYNAMIC"
      }' \
  $BASE_URL/customers/)

CUSTOMER_ID=$(echo $NEW_CUSTOMER_RESPONSE | jq -r .id)
echo "Captured new Customer ID: $CUSTOMER_ID"
echo $NEW_CUSTOMER_RESPONSE | jq .


# --- Create a Product (as Admin) and Capture ID ---
print_header "Creating a new Product (as Admin)"
NEW_PRODUCT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
        "product_code": "DYN-PROD-001",
        "name": "Dynamic Test Product",
        "description": "A product created by the test script",
        "price": 99.99,
        "stock": 50
      }' \
  $BASE_URL/products/)

PRODUCT_ID=$(echo $NEW_PRODUCT_RESPONSE | jq -r .id)
echo "Captured new Product ID: $PRODUCT_ID"
echo $NEW_PRODUCT_RESPONSE | jq .


# --- Create an Invoice (as Admin) and Capture ID ---
print_header "Creating a new Invoice (as Admin)"
NEW_INVOICE_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
        "customer_id": '$CUSTOMER_ID',
        "invoice_date": "2024-08-15",
        "due_date": "2024-09-15",
        "items": [
            {"product_id": '$PRODUCT_ID', "quantity": 2}
        ]
      }' \
  $BASE_URL/invoices/)

INVOICE_ID=$(echo $NEW_INVOICE_RESPONSE | jq -r .id)
echo "Captured new Invoice ID: $INVOICE_ID"
echo $NEW_INVOICE_RESPONSE | jq .


# ==============================================================================
#                       STANDARD USER FLOW
# ==============================================================================

# --- Standard User Login ---
print_header "Attempting to log in as Standard User to get User Token"
USER_LOGIN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "email": "'$USER_EMAIL'",
        "password": "'$USER_PASSWORD'"
      }' \
  $BASE_URL/auth/login)

USER_TOKEN=$(echo $USER_LOGIN_RESPONSE | jq -r .access_token)

if [ "$USER_TOKEN" == "null" ] || [ -z "$USER_TOKEN" ]; then
    echo "Failed to get User Token. The server responded with:"
    echo $USER_LOGIN_RESPONSE | jq .
    echo "Skipping user-specific tests."
else
    echo "Successfully retrieved User Token."
    
    # --- Get Current User Profile ---
    print_header "Get Current User Profile (as Standard User)"
    curl -s -X GET \
      -H "Authorization: Bearer $USER_TOKEN" \
      $BASE_URL/users/me | jq .

    # --- Get Dashboard ---
    print_header "Get Dashboard data (as Standard User)"
    curl -s -X GET \
      -H "Authorization: Bearer $USER_TOKEN" \
      $BASE_URL/dashboard | jq .
fi


# ==============================================================================
#                       CLEANUP
# ==============================================================================

print_header "Cleaning up created resources (as Admin)"

# --- Bulk Delete Invoice ---
echo "Deleting Invoice with ID: $INVOICE_ID"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"ids": ['$INVOICE_ID']}' \
  $BASE_URL/invoices/bulk-delete | jq .

# --- Bulk Delete Customer ---
echo "Deleting Customer with ID: $CUSTOMER_ID"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"ids": ['$CUSTOMER_ID']}' \
  $BASE_URL/customers/bulk-delete | jq .
  
# --- Bulk Delete Product ---
echo "Deleting Product with ID: $PRODUCT_ID"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"ids": ['$PRODUCT_ID']}' \
  $BASE_URL/products/bulk-delete | jq .

print_header "Script finished."

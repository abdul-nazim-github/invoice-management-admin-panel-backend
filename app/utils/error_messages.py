
# app/utils/error_messages.py

ERROR_MESSAGES = {
    "validation": {
        "request_body_empty": "Request body cannot be empty.",
        "missing_credentials": "Email and password are required.",
        "missing_fields": "Missing required fields.",
        "invalid_input": "Invalid input provided. Please check the data types and formats.",
    },
    "not_found": {
        "customer": "Customer not found.",
        "product": "Product not found.",
        "invoice": "Invoice not found.",
        "payment": "Payment not found.",
        "user": "The requested user could not be found."
    },
    "server_error": {
        "create_customer": "An unexpected error occurred while creating the customer.",
        "fetch_customer": "An unexpected error occurred while fetching customer(s).",
        "update_customer": "An unexpected error occurred while updating the customer.",
        "delete_customer": "An unexpected error occurred while deleting the customer.",
        
        "create_product": "An unexpected error occurred while creating the product.",
        "fetch_product": "An unexpected error occurred while fetching product(s).",
        "update_product": "An unexpected error occurred while updating the product.",
        "delete_product": "An unexpected error occurred while deleting the product.",
        
        "create_invoice": "An unexpected error occurred while creating the invoice.",
        "fetch_invoice": "An unexpected error occurred while fetching invoice(s).",
        "update_invoice": "An unexpected error occurred while updating the invoice.",
        "delete_invoice": "An unexpected error occurred while deleting the invoice.",
        
        "create_payment": "An unexpected error occurred while creating the payment.",
        "fetch_payment": "An unexpected error occurred while fetching payment(s).",

        "create_user": "Could not create user.",
        "fetch_user": "An unexpected error occurred while fetching user(s).",
        "update_user": "An unexpected error occurred while updating the user.",
        "delete_user": "An unexpected error occurred while deleting the user."
    },
    "auth": {
        "invalid_token": "Invalid or expired token. Please log in again.",
        "missing_token": "Missing authorization token. Please provide a valid token.",
        "unauthorized": "Unauthorized access. You do not have permission to perform this action.",
        "login_failed": "Login failed. Please check your email and password."
    },
    "conflict": {
        "user_exists": "A user with this email address already exists."
    }
}

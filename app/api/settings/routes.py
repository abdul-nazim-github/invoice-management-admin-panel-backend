from flask import request
from . import settings_bp
from app.database.models.user_model import (
    update_user_profile,
    update_user_password,
    update_user_billing,
    find_user_by_id,
)
from app.utils.response import success_response, error_response
import bcrypt

@settings_bp.route("/profile/<user_id>", methods=["PUT"])
def handle_update_profile(user_id):
    """Updates user profile information (name, email)."""
    data = request.get_json()
    if not data:
        return error_response("validation_error", "Invalid JSON provided.")

    # Validate that the user exists
    if not find_user_by_id(user_id):
        return error_response("not_found", f"User with ID '{user_id}' not found.")

    # Dynamically build the fields to update
    fields_to_update = {}
    if "name" in data:
        fields_to_update["name"] = data["name"]
    if "email" in data:
        fields_to_update["email"] = data["email"]

    if not fields_to_update:
        return error_response(
            "validation_error", "No valid fields (name, email) provided for update."
        )

    try:
        updated_user = update_user_profile(user_id, **fields_to_update)
        if updated_user:
            return success_response(updated_user, "Profile updated successfully.")
        return error_response(
            "server_error", "An unexpected error occurred while updating the profile."
        )
    except Exception as e:
        return error_response("server_error", f"Failed to update profile: {e}")

@settings_bp.route("/profile/password/<user_id>", methods=["PUT"])
def handle_update_password(user_id):
    """Updates a user's password."""
    data = request.get_json()
    password = data.get("password")

    if not password:
        return error_response("validation_error", "Password is required.")

    if not find_user_by_id(user_id):
        return error_response("not_found", f"User with ID '{user_id}' not found.")

    try:
        # Hash the new password before storing it
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        success = update_user_password(user_id, hashed_password.decode("utf-8"))
        if success:
            return success_response(message="Password updated successfully.")
        return error_response("server_error", "Failed to update password.")
    except Exception as e:
        return error_response("server_error", f"An unexpected error occurred: {e}")

@settings_bp.route("/billing/<user_id>", methods=["PUT"])
def handle_update_billing(user_id):
    """Updates user billing details."""
    data = request.get_json()
    if not data:
        return error_response("validation_error", "Invalid JSON provided.")

    if not find_user_by_id(user_id):
        return error_response("not_found", f"User with ID '{user_id}' not found.")

    # Extract billing fields from the request
    billing_info = {
        "address": data.get("billing_address"),
        "city": data.get("billing_city"),
        "state": data.get("billing_state"),
        "pin": data.get("billing_pin"),
        "gst": data.get("billing_gst"),
    }

    # Filter out any fields that were not provided in the request
    update_data = {k: v for k, v in billing_info.items() if v is not None}

    if not update_data:
        return error_response("validation_error", "No billing fields provided for update.")

    try:
        updated_user = update_user_billing(user_id, **update_data)
        if updated_user:
            return success_response(updated_user, "Billing details updated successfully.")
        return error_response("server_error", "Failed to update billing details.")
    except Exception as e:
        return error_response("server_error", f"An unexpected error occurred: {e}")

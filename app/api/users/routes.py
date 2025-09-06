# =============================
# app/api/users/routes.py (profile/settings)
# =============================
from flask import Blueprint, request, jsonify
from passlib.hash import bcrypt
from app.utils.auth import require_auth
from app.database.models.user_model import update_user_profile, update_user_password, update_user_billing, find_user_by_id

users_bp = Blueprint("users", __name__)


@users_bp.get("/me")
@require_auth
def me():
    user = find_user_by_id(request.user["sub"]) or {}
    public = {k: user.get(k) for k in ["id", "email", "username", "name", "role", "bill_address", "bill_city", "bill_state", "bill_pin", "bill_gst"]}
    return jsonify(public)


@users_bp.put("/profile")
@require_auth
def update_profile():
    data = request.json
    update_user_profile(request.user["sub"], name=data.get("name"), email=data.get("email"))
    return jsonify({"message": "profile updated"})


@users_bp.put("/password")
@require_auth
def change_password():
    data = request.json
    new_hash = bcrypt.hash(data["new_password"])
    update_user_password(request.user["sub"], new_hash)
    return jsonify({"message": "password updated"})


@users_bp.put("/billing")
@require_auth
def update_billing():
    data = request.json
    update_user_billing(
        request.user["sub"],
        addr=data.get("bill_address"),
        city=data.get("bill_city"),
        state=data.get("bill_state"),
        pin=data.get("bill_pin"),
        gst=data.get("bill_gst"),
    )
    return jsonify({"message": "billing updated"})

# app/routes/dashboard.py
from flask import Blueprint, jsonify
from app.database.models.dashboard_model import get_dashboard_stats, get_sales_performance
from app.utils.response import success_response
from app.utils.auth import token_required

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    """
    Endpoint to get dashboard statistics.
    Accessible only by authenticated users.
    """
    # You can add role checks here if needed, e.g.:
    # if current_user['role'] != 'admin':
    #     return error_response("unauthorized", "Admin access required", status=403)

    dashboard_stats = get_dashboard_stats()
    sales_performance = get_sales_performance()

    combined_stats = {
        **dashboard_stats,
        "sales_performance": sales_performance,
    }

    return success_response(result=combined_stats, message="Dashboard stats retrieved successfully.")

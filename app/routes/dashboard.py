# app/routes/dashboard.py
from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.database.models.dashboard_model import get_dashboard_stats, get_sales_performance, get_latest_invoices
from app.utils.response import success_response
from app.utils.auth import require_admin

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@require_admin
def get_stats():
    """
    Endpoint to get dashboard statistics.
    Accessible only by authenticated admins.
    """
    dashboard_stats = get_dashboard_stats()
    sales_performance = get_sales_performance()
    latest_invoices = get_latest_invoices()

    combined_stats = {
        **dashboard_stats,
        "sales_performance": sales_performance,
        "latest_invoices": latest_invoices
    }

    return success_response(result=combined_stats, message="Dashboard stats retrieved successfully.")

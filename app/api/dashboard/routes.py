# app/api/dashboard/routes.py
from flask import Blueprint
from app.utils.auth import require_auth
from app.database.models.dashboard_model import get_dashboard_stats, get_sales_performance
from app.utils.response import error_response, success_response

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/stats")
@require_auth
def dashboard_stats():
    try:
        stats = get_dashboard_stats()
        return success_response(
            message="Dashboard fetched successfully",
            result=stats,
        )
    except Exception as e:
        return error_response(
            type="server_error",
            message="Something went wrong",
            details={"exception": [str(e)]},
            status=500,
        )

@dashboard_bp.get("/sales-performance")
@require_auth
def sales_performance():
    data = get_sales_performance()
    return success_response(
            message="Sales performance fetch successfully",
            result={"sales_performance": data},
        )
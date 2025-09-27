from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.models.user import User
from app.utils.response import success_response, error_response
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.auth import require_admin
from app.utils.pagination import get_pagination

users_blueprint = Blueprint('users', __name__)

@users_blueprint.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    if user:
        return success_response(user.to_dict(), message="User profile retrieved successfully")
    return error_response('not_found', message=ERROR_MESSAGES["not_found"]["user"], status=404)

@users_blueprint.route('/users', methods=['GET'])
@jwt_required()
@require_admin
def get_users():
    page, per_page = get_pagination()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        users, total = User.find_with_pagination_and_count(page=page, per_page=per_page, include_deleted=include_deleted)
        return success_response({
            'users': [u.to_dict() for u in users],
            'total': total,
            'page': page,
            'per_page': per_page
        }, message="Users retrieved successfully")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_user"], details=str(e), status=500)

@users_blueprint.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)

    # A user can get their own info, or an admin can get any user's info
    if not (user.is_admin or current_user_id == user_id):
        return error_response('forbidden', message=ERROR_MESSAGES["forbidden"], status=403)

    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    try:
        user = User.find_by_id(user_id, include_deleted=include_deleted)
        if user:
            return success_response(user.to_dict(), message="User retrieved successfully")
        return error_response('not_found', message=ERROR_MESSAGES["not_found"]["user"], status=404)
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["fetch_user"], details=str(e), status=500)

@users_blueprint.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    # A user can update their own info, or an admin can update any user's info
    if not (user.is_admin or current_user_id == user_id):
        return error_response('forbidden', message=ERROR_MESSAGES["forbidden"], status=403)
        
    data = request.get_json()
    if not data:
        return error_response('validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)

    try:
        if not User.update(user_id, data):
            return error_response('not_found', message=ERROR_MESSAGES["not_found"]["user"], status=404)

        updated_user = User.find_by_id(user_id)
        return success_response(updated_user.to_dict(), message="User updated successfully")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["update_user"], details=str(e), status=500)

@users_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_user(user_id):
    try:
        if not User.soft_delete(user_id):
            return error_response('not_found', message=ERROR_MESSAGES["not_found"]["user"], status=404)

        return success_response(message="User soft-deleted successfully")
    except Exception as e:
        return error_response('server_error', message=ERROR_MESSAGES["server_error"]["delete_user"], details=str(e), status=500)

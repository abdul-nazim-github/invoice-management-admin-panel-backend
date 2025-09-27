from flask import Blueprint, request, jsonify
from app.database.models.user import User

users_blueprint = Blueprint('users', __name__)

@users_blueprint.route('/users', methods=['GET'])
def get_users():
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    users = User.find_all(include_deleted=include_deleted)
    return jsonify([user.to_dict() for user in users])

@users_blueprint.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    user = User.find_by_id(user_id, include_deleted=include_deleted)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'message': 'User not found'}), 404

@users_blueprint.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    # The BaseModel update method does not return the object
    User.update(user_id, data)
    user = User.find_by_id(user_id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'message': 'User not found'}), 404

@users_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if User.soft_delete(user_id):
        return jsonify({'message': 'User soft-deleted'})
    return jsonify({'message': 'User not found'}), 404

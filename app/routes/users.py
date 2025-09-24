from flask import Blueprint, request, jsonify
from app.database.models.user import User

users_blueprint = Blueprint('users', __name__)

@users_blueprint.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User.create(data)
    return jsonify(user), 201

@users_blueprint.route('/users', methods=['GET'])
def get_users():
    users = User.get_all()
    return jsonify(users)

@users_blueprint.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.get_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({'message': 'User not found'}), 404

@users_blueprint.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User.update(user_id, data)
    if user:
        return jsonify(user)
    return jsonify({'message': 'User not found'}), 404

@users_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if User.delete(user_id):
        return jsonify({'message': 'User deleted'})
    return jsonify({'message': 'User not found'}), 404

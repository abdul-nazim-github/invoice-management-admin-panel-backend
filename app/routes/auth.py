from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from app.database.models.user import User
from app.utils.auth import require_auth, require_admin

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user and returns a JWT access token.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.find_by_email(email)

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"message": "Invalid credentials"}), 401

@auth_blueprint.route('/register', methods=['POST'])
@require_auth
@require_admin
def register():
    """
    Registers a new user.
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is empty"}), 400
    
    required_fields = ['username', 'email', 'password', 'name']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    if User.find_by_email(data['email']):
        return jsonify({"message": "User with this email already exists"}), 409

    try:
        user = User.create(data)
        return jsonify(user.to_dict()), 201
    except Exception as e:
        return jsonify({"message": "Could not create user", "error": str(e)}), 500

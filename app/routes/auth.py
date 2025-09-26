from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from app.database.models.user import User

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

    # In a real app, you would query the database for the user
    # For this example, we'll use a mock user from the User model
    user = User.find_by_email(email)

    if user and user.check_password(password):
        # Correctly create an access token with the user's identity
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"message": "Invalid credentials"}), 401

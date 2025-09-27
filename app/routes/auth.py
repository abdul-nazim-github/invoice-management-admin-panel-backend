from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from app.database.models.user import User
from app.utils.auth import require_admin
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.response import error_response

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user and returns a JWT access token.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return error_response(type='validation_error', message=ERROR_MESSAGES["validation"]["missing_credentials"], status=400)

    email = data.get('email')
    password = data.get('password')

    user = User.find_by_email(email)

    if user and user.check_password(password):
        # Include the user's role in the JWT claims
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200
    
    return error_response(type='invalid_credentials', message=ERROR_MESSAGES["auth"]["invalid_credentials"], status=401)

@auth_blueprint.route('/register', methods=['POST'])
@jwt_required()
@require_admin
def register():
    """
    Registers a new user. This is an admin-only action.
    """
    data = request.get_json()
    if not data:
        return error_response(type='validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)
    
    required_fields = ['username', 'email', 'password', 'name']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response(type='validation_error', message=f"Missing required fields: {', '.join(missing_fields)}", status=400)

    if User.find_by_email(data['email']):
        return error_response(type='conflict', message=ERROR_MESSAGES["conflict"]["user_exists"], status=409)

    try:
        user = User.create(data)
        return jsonify(user.to_dict()), 201
    except Exception as e:
        return error_response(type='server_error', message=ERROR_MESSAGES["server_error"]["create_user"], status=500)

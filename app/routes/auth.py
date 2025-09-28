from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from pymysql.err import IntegrityError
from app.database.models.user import User
from app.database.token_blocklist import BLOCKLIST
from app.utils.auth import require_admin
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.response import error_response

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/sign-in', methods=['POST'])
def sign_in():
    """
    Authenticates a user and returns a JWT access token.
    """
    data = request.get_json()
    if not data:
        return error_response(type='validation_error', message="Request body cannot be empty.", status=400)

    login_identifier = data.get('email') or data.get('username')
    password = data.get('password')

    if not login_identifier or not password:
        return error_response(type='validation_error', message=ERROR_MESSAGES["validation"]["missing_credentials"], status=400)

    user = User.find_by_username_or_email(login_identifier)

    if user and user.check_password(password):
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200
    
    return error_response(type='invalid_credentials', message=ERROR_MESSAGES["auth"]["invalid_credentials"], status=401)

@auth_blueprint.route('/sign-out', methods=['POST'])
@jwt_required()
def sign_out():
    """
    Signs out the user by adding the token's JTI to the blocklist.
    """
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify(message="Successfully signed out."), 200

@auth_blueprint.route('/register', methods=['POST'])
@jwt_required()
@require_admin
def register():
    """
    Registers a new user. This is an admin-only action.
    Handles validation, duplicate checks, and potential race conditions.
    """
    data = request.get_json()
    if not data:
        return error_response(type='validation_error', message=ERROR_MESSAGES["validation"]["request_body_empty"], status=400)
    
    required_fields = ['username', 'email', 'password', 'name']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response(type='validation_error', message=f"Missing required fields: {', '.join(missing_fields)}", status=400)

    # Proactive checks for existing username or email
    if User.find_by_username(data['username']):
        return error_response(type='conflict', message="Username already exists.", status=409)
    if User.find_by_email(data['email']):
        return error_response(type='conflict', message="Email already exists.", status=409)

    try:
        user = User.create(data)
        if user is None:
             return error_response(type='server_error', message=ERROR_MESSAGES["server_error"]["create_user"], status=500)
        return jsonify(user.to_dict()), 201
        
    except IntegrityError:
        # This catches the race condition if a user is created between the check and the create call
        return error_response(type='conflict', message="Username or email already exists.", status=409)
    except Exception as e:
        # Catch any other unexpected errors during user creation
        return error_response(type='server_error', message=str(e), status=500)

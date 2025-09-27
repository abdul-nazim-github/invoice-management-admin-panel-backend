import os
from flask import Flask
from flask_jwt_extended import JWTManager
from app.database.models.user import User
from app.utils.error_messages import ERROR_MESSAGES
from app.utils.response import error_response

# Import blueprints from their correct locations
from .routes.auth import auth_blueprint
from .routes.users import users_blueprint
from .routes.customers import customers_blueprint
from .routes.invoices import invoices_blueprint
from .routes.products import products_blueprint

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', 'default-super-secret-key')
    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'default-another-super-secret-key')
    
    # Initialize extensions
    jwt = JWTManager(app)

    # --- JWT Custom Error Handlers ---
    # Reverted to using decorators for robust error handling.
    # The Pylance "unused function" warnings on these callbacks are incorrect and can be safely ignored.

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handles cases where the token is invalid (e.g., malformed)."""
        return error_response(type='invalid_token', message=ERROR_MESSAGES["auth"]["invalid_token"], status=401)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handles requests that are missing an authorization token."""
        return error_response(type='missing_token', message=ERROR_MESSAGES["auth"]["missing_token"], status=401)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handles expired tokens."""
        return error_response(type='token_expired', message=ERROR_MESSAGES["auth"]["invalid_token"], status=401)

    @jwt.user_lookup_error_loader
    def user_lookup_error_callback(jwt_header, jwt_data):
        """Handles cases where the user from the token cannot be found in the database."""
        return error_response(type='invalid_token', message=ERROR_MESSAGES["auth"]["invalid_token"], status=401)

    # --- JWT User Claims ---
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.find_by_id(identity)

    # --- Register Blueprints ---
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
    app.register_blueprint(users_blueprint, url_prefix='/api')
    app.register_blueprint(customers_blueprint, url_prefix='/api')
    app.register_blueprint(invoices_blueprint, url_prefix='/api')
    app.register_blueprint(products_blueprint, url_prefix='/api')

    # A simple health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}

    return app

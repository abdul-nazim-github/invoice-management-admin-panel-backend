import os
from flask import Flask
from flask_jwt_extended import JWTManager
from app.database.models.user import User

# Import blueprints from their correct locations
from .routes.auth import auth_blueprint
from .routes.users import users_blueprint
from .routes.customers import customers_blueprint
from .routes.invoices import invoices_blueprint
from .routes.payments import payments_blueprint
from .routes.products import products_blueprint

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    # Load the secret key from environment variables for better security
    # Fallback to a default, insecure key for development if not set
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', 'default-super-secret-key')
    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'default-another-super-secret-key')
    
    # Initialize extensions
    jwt = JWTManager(app)

    # --- JWT User Claims ---
    # This function is called whenever a protected endpoint is accessed,
    # and it adds the user's role to the JWT claims.
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.find_by_id(identity)

    # --- Register Blueprints ---
    # The new auth blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
    
    # The existing user blueprint (assuming it might be used for user management)
    app.register_blueprint(users_blueprint, url_prefix='/api')
    
    # Other blueprints from your project structure
    app.register_blueprint(customers_blueprint, url_prefix='/api')
    app.register_blueprint(invoices_blueprint, url_prefix='/api')
    app.register_blueprint(payments_blueprint, url_prefix='/api')
    app.register_blueprint(products_blueprint, url_prefix='/api')

    # A simple health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}

    return app

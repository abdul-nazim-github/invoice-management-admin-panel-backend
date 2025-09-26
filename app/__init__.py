from flask import Flask
from flask_jwt_extended import JWTManager
from .utils.cache import cache

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
    # For JWT, a secret key is required. This should be in your instance config.
    # For demonstration, we'll set a simple one here.
    # IMPORTANT: Change this in a real application!
    app.config["JWT_SECRET_KEY"] = "super-secret-key-change-me"
    app.config["SECRET_KEY"] = "another-super-secret-key-change-me"
    
    # Initialize extensions
    jwt = JWTManager(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

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

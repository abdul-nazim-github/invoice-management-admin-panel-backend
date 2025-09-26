from flask import Flask
from .utils.cache import cache
from app.api.auth.routes import auth_bp
from app.api.users.routes import users_bp
from .routes.customers import customers_blueprint
from .routes.invoices import invoices_blueprint
from .routes.payments import payments_blueprint
from .routes.products import products_blueprint
from .api.dashboard.routes import dashboard_bp
from app.database.schema import create_schema

def create_app():
    app = Flask(__name__)

    # Initialize the cache with the app
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})
    
    create_schema()

    # Import and register your Blueprints here
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(customers_blueprint, url_prefix='/api')
    app.register_blueprint(invoices_blueprint, url_prefix='/api')
    app.register_blueprint(payments_blueprint, url_prefix='/api')
    app.register_blueprint(products_blueprint, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    return app

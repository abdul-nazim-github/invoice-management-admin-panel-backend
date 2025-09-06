from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.database import init_db

def create_app():
    load_dotenv()
    init_db()
    app = Flask(__name__)

    app.config["JWT_SECRET"] = os.getenv("JWT_SECRET", "change-this-secret")
    app.config["JWT_EXPIRES_MIN"] = int(os.getenv("JWT_EXPIRES_MIN", "1440"))

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.api.auth.routes import auth_bp
    from app.api.dashboard.routes import dashboard_bp
    from app.api.customers.routes import customers_bp
    from app.api.products.routes import products_bp
    from app.api.invoices.routes import invoices_bp
    from app.api.users.routes import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(customers_bp, url_prefix="/api/customers")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(invoices_bp, url_prefix="/api/invoices")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app

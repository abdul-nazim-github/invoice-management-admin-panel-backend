from flask import Flask
from app.routes.users import users_blueprint
from app.routes.customers import customers_blueprint
from app.routes.products import products_blueprint
from app.routes.invoices import invoices_blueprint
from app.routes.payments import payments_blueprint

def create_app():
    app = Flask(__name__)

    app.register_blueprint(users_blueprint)
    app.register_blueprint(customers_blueprint)
    app.register_blueprint(products_blueprint)
    app.register_blueprint(invoices_blueprint)
    app.register_blueprint(payments_blueprint)

    return app

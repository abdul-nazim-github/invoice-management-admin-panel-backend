import mysql.connector
from app.database.config import Config

def get_db_connection():
    """Establishes a database connection using the settings from Config."""
    # Unpack the configuration dictionary directly into the connect function
    return mysql.connector.connect(**Config.MYSQL_CONFIG)

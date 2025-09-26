import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

class Config:
    """
    Database configuration class.
    
    This class encapsulates the settings required to connect to the database,
    loading sensitive information from environment variables.
    """
    
    # The full configuration dictionary for the MySQL connection
    MYSQL_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", "root"),
        "database": os.getenv("DB_NAME", "vyaper_billing_db"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }

    @staticmethod
    def get_db_settings():
        """A static method to easily retrieve the database settings."""
        return Config.MYSQL_CONFIG

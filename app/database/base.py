
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection(db_required=True):
    """
    Establishes a connection to the MySQL database.
    If db_required is False, it connects to the MySQL server without specifying a database.
    """
    host = os.environ.get('DB_HOST', 'localhost')
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '') # Default to empty string if not set
    db_name = os.environ.get('DB_NAME', 'invoice_db')

    # Connection arguments
    conn_args = {
        'host': host,
        'user': user,
        'password': password,
        'cursorclass': pymysql.cursors.DictCursor
    }

    # Only add the database to the connection args if it's required
    if db_required:
        conn_args['database'] = db_name
    
    return pymysql.connect(**conn_args)


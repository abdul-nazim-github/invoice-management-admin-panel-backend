import os
import logging
from app.database.base import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_schemas():
    """
    Reads all .sql files in the current directory, splits them into
    individual statements, and executes them one by one to create the
    database schema.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            schema_dir = os.path.dirname(__file__)
            for filename in os.listdir(schema_dir):
                if filename.endswith('.sql'):
                    filepath = os.path.join(schema_dir, filename)
                    logging.info(f"Processing schema file: {filepath}")
                    with open(filepath, 'r') as f:
                        sql_script = f.read()
                        
                        # Split commands and filter out empty ones
                        sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
                        
                        logging.info(f"Found {len(sql_commands)} SQL commands to execute.")
                        
                        # Execute each command
                        for command in sql_commands:
                            logging.info(f"Executing SQL: {command}")
                            try:
                                cursor.execute(command)
                            except Exception as e:
                                logging.error(f"Failed to execute command: {command}")
                                logging.error(f"Error: {e}")
                                raise # Re-raise the exception to see the traceback
        conn.commit()
        logging.info("Database schema creation/update successful.")
    except Exception as e:
        logging.error(f"An error occurred during schema creation: {e}")
        raise
    finally:
        conn.close()

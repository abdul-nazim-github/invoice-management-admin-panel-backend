import os
from app.database.base import get_db_connection

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
                    with open(filepath, 'r') as f:
                        # Read the entire SQL script
                        sql_script = f.read()
                        
                        # Split the script into individual commands at the semicolon
                        # and filter out any empty strings that may result.
                        sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
                        
                        # Execute each command separately
                        for command in sql_commands:
                            cursor.execute(command)
        conn.commit()
    finally:
        conn.close()

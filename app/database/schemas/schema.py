import os
from app.database.base import get_db_connection

def create_schemas():
    """
    Reads and executes the schema.sql file to create the database schema.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Construct the full path to the schema.sql file
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            # Check if the schema.sql file exists before proceeding
            if not os.path.exists(schema_path):
                print(f"Schema file not found at: {schema_path}")
                return

            with open(schema_path, 'r') as f:
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

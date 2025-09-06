import os
from app.database.models.base import get_db_connection

def create_schemas():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Get the directory of the current script
        schema_dir = os.path.dirname(__file__)
        # List all files in the directory
        for filename in os.listdir(schema_dir):
            # Check if the file is a SQL file
            if filename.endswith('.sql'):
                # Construct the full file path
                filepath = os.path.join(schema_dir, filename)
                # Open and read the SQL file
                with open(filepath, 'r') as f:
                    sql = f.read()
                    # Execute the SQL command
                    cursor.execute(sql)
    conn.commit()
    conn.close()

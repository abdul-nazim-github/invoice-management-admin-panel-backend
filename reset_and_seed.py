
import pymysql
from app.database.base import get_db_connection
from seed import seed_initial_admin, create_tables

def reset_database():
    """
    Drops the database if it exists and recreates it.
    """
    try:
        # We need a connection to the MySQL server, but not to a specific DB
        conn = get_db_connection(db_required=False)
        
        # We need to get the DB_NAME from our environment to drop it
        import os
        from dotenv import load_dotenv
        load_dotenv()
        db_name = os.getenv("DB_NAME", "invoice_db")

        with conn.cursor() as cursor:
            print(f"Dropping database `{db_name}` if it exists...")
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            print(f"Creating database `{db_name}`...")
            cursor.execute(f"CREATE DATABASE `{db_name}`")
        print("Database has been reset.")
    except pymysql.MySQLError as e:
        print(f"A database error occurred during reset: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        # 1. Reset the entire database
        reset_database()
        
        # 2. Run the seeding process which will now also create the tables
        print("Starting the seeding process...")
        seed_initial_admin()
        print("Seeding process completed.")
        
    except Exception as e:
        print(f"An error occurred during the reset and seed process: {e}")

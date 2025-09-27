
import pymysql
from app.database.base import get_db_connection
from seed import create_tables_from_schema, seed_initial_admin
import os

def reset_and_seed_database():
    """Drops the database, recreates it, creates tables, and seeds the admin user."""
    conn = None
    try:
        db_name = os.getenv("DB_NAME", "invoice_db")

        # 1. Connect to MySQL server and recreate the database
        conn = get_db_connection(db_required=False)
        with conn.cursor() as cursor:
            print(f"Dropping database `{db_name}` if it exists...")
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            print(f"Creating database `{db_name}`...")
            cursor.execute(f"CREATE DATABASE `{db_name}`")
        conn.close() # Close the connection
        print("Database has been reset.")

        # At this point, subsequent connections via get_db_connection() will connect
        # to the correct, newly created database.

        # 2. Create all tables by executing the schema
        print("Creating all tables from schema...")
        create_tables_from_schema()
        
        # 3. Seed the initial admin user
        print("Seeding initial admin user...")
        seed_initial_admin()
        
        print("Database initialization and seeding process completed successfully.")

    except pymysql.MySQLError as e:
        print(f"A database error occurred during reset and seed: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during reset and seed: {e}")
        raise
    finally:
        # Ensure the connection is closed even if errors occur
        if conn and conn.open:
            conn.close()

if __name__ == "__main__":
    try:
        reset_and_seed_database()
    except Exception as e:
        print(f"An error occurred during the standalone reset and seed process: {e}")


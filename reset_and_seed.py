
import pymysql
from app.database.base import get_db_connection
from seed import seed_initial_admin
import os

def reset_and_seed_database():
    """Drops the database, recreates it, and seeds it with the initial admin user."""
    conn = None
    try:
        # Get DB name from environment, with a fallback
        db_name = os.getenv("DB_NAME", "invoice_db")

        # Connect to MySQL server without specifying a database
        conn = get_db_connection(db_required=False)
        with conn.cursor() as cursor:
            print(f"Dropping database `{db_name}` if it exists...")
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            print(f"Creating database `{db_name}`...")
            cursor.execute(f"CREATE DATABASE `{db_name}`")
        print("Database has been reset.")

        # Now that the database exists, we can seed it.
        print("Starting the seeding process...")
        seed_initial_admin() # This will create tables and the admin user
        print("Seeding process completed.")

    except pymysql.MySQLError as e:
        print(f"A database error occurred during reset and seed: {e}")
        # Re-raise the exception to halt the application if the DB setup fails
        raise
    finally:
        if conn:
            conn.close()

# This block allows the script to be run directly from the command line if needed
if __name__ == "__main__":
    try:
        reset_and_seed_database()
    except Exception as e:
        print(f"An error occurred during the reset and seed process: {e}")


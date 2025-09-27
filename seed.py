
import pymysql
import os
from app.database.db_manager import DBManager
from werkzeug.security import generate_password_hash

# --- Default Admin User Details ---
ADMIN_EMAIL = "admin@example.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"
ADMIN_ROLE = "admin"
ADMIN_NAME = "Administrator"

def create_tables_from_schema():
    """
    Reads the schema.sql file and executes it to create all tables.
    """"""
    # Construct the absolute path to the schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'app', 'database', 'schemas', 'schema.sql')
    print(f"Reading database schema from: {schema_path}")

    try:
        with open(schema_path, 'r') as f:
            # Read the entire file and split into individual statements
            sql_statements = f.read().split(';')

        for statement in sql_statements:
            # Ignore empty statements that can result from splitting
            if statement.strip():
                # Use the write query method as it handles execution without fetching results
                DBManager.execute_write_query(statement)
        
        print("All tables from schema.sql have been created or already exist.")

    except FileNotFoundError:
        print(f"ERROR: The schema file was not found at {schema_path}")
        raise
    except Exception as e:
        print(f"An error occurred while creating tables from schema: {e}")
        raise

def seed_initial_admin():
    """
    Creates the first admin user using the DBManager if no admin exists.
    This function now assumes that all tables have already been created.
    """
    try:
        # All tables are now created by create_tables_from_schema(), 
        # which is called from reset_and_seed.py before this function.

        # Check if an admin user already exists
        admin_user = DBManager.execute_query(
            "SELECT id FROM users WHERE role = %s", (ADMIN_ROLE,), fetch='one'
        )

        if admin_user:
            print("An admin user already exists. Seeding not required.")
            return

        print(f"No admin user found. Creating initial admin: {ADMIN_EMAIL}")

        # Hash the password with scrypt
        password_hash = generate_password_hash(ADMIN_PASSWORD, method='scrypt')

        # Insert the new admin user
        sql = """
        INSERT INTO users (username, email, password_hash, name, role)
        VALUES (%s, %s, %s, %s, %s)
        """
        user_id = DBManager.execute_write_query(sql, (ADMIN_USERNAME, ADMIN_EMAIL, password_hash, ADMIN_NAME, ADMIN_ROLE))

        if user_id:
            print("=" * 50)
            print("Default admin user created successfully!")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Password: {ADMIN_PASSWORD}")
            print("=" * 50)
        else:
            print("Failed to create the admin user.")

    except pymysql.MySQLError as e:
        print(f"A database error occurred during admin seeding: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during admin seeding: {e}")

# This block is for standalone execution if needed
if __name__ == "__main__":
    # In a standalone run, we would need to establish a db connection context
    print("This script is intended to be called by reset_and_seed.py")
    print("Running create_tables_from_schema and seed_initial_admin...")
    try:
        create_tables_from_schema()
        seed_initial_admin()
        print("Standalone seeding process completed.")
    except Exception as e:
        print(f"An error occurred during standalone seeding: {e}")

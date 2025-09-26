
import pymysql
from werkzeug.security import generate_password_hash
from app.database.base import get_db_connection

# --- Default Admin User Details ---
ADMIN_EMAIL = "admin@example.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"
ADMIN_ROLE = "admin"
ADMIN_NAME = "Administrator"

def seed_initial_admin():
    """
    Creates the very first admin user in the database if no admin exists.
    This allows the application to be bootstrapped.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if an admin user already exists
            cursor.execute("SELECT id FROM users WHERE role = %s", (ADMIN_ROLE,))
            if cursor.fetchone():
                print(f"An admin user already exists. Seeding not required.")
                return

            # If no admin, create the initial one
            print(f"No admin user found. Creating initial admin: {ADMIN_EMAIL}")
            
            # Hash the password for security
            password_hash = generate_password_hash(ADMIN_PASSWORD)

            # Insert the new admin user
            sql = """
            INSERT INTO users (username, email, password_hash, name, role)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (ADMIN_USERNAME, ADMIN_EMAIL, password_hash, ADMIN_NAME, ADMIN_ROLE))
            conn.commit()
            
            print("="*50)
            print("Default admin user created successfully!")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Password: {ADMIN_PASSWORD}")
            print("="*50)
            print("You can now run the application and log in with these credentials.")

    except pymysql.MySQLError as e:
        print(f"A database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    seed_initial_admin()

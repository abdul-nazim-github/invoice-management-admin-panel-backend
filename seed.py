
import pymysql
from app.database.db_manager import DBManager

# --- Default Admin User Details ---
ADMIN_EMAIL = "admin@example.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"
ADMIN_ROLE = "admin"
ADMIN_NAME = "Administrator"

def create_tables():
    """Create database tables if they do not exist."""
    # SQL to create the 'users' table.
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(100),
        role ENUM('admin', 'staff') DEFAULT 'staff',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deleted_at TIMESTAMP NULL
    );
    """
    try:
        # Using a method that can execute raw SQL without returning rows
        DBManager.execute_write_query(create_users_table_sql)
        print("`users` table created or already exists.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def seed_initial_admin():
    """
    Creates the first admin user using the DBManager if no admin exists.
    """
    try:
        # First, ensure tables are created
        create_tables()

        # Check if an admin user already exists using DBManager
        admin_user = DBManager.execute_query(
            "SELECT id FROM users WHERE role = %s", (ADMIN_ROLE,), fetch='one'
        )

        if admin_user:
            print("An admin user already exists. Seeding not required.")
            return

        print(f"No admin user found. Creating initial admin: {ADMIN_EMAIL}")

        # Use the User model's create method, which handles hashing and uses DBManager
        from app.database.models.user import User
        user_data = {
            'username': ADMIN_USERNAME,
            'email': ADMIN_EMAIL,
            'password': ADMIN_PASSWORD,
            'name': ADMIN_NAME,
            'role': ADMIN_ROLE
        }
        
        # The User.create method should handle everything
        created_user = User.create(user_data)

        if created_user:
            print("=" * 50)
            print("Default admin user created successfully!")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Password: {ADMIN_PASSWORD}")
            print("=" * 50)
            print("You can now run the application and log in with these credentials.")
        else:
            print("Failed to create the admin user for an unknown reason.")

    except pymysql.MySQLError as e:
        print(f"A database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    seed_initial_admin()


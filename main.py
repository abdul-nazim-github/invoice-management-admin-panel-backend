from app import create_app
from app.database.schemas.schema import create_schemas
from seed import seed_initial_admin

# Create the database schema before running the app
create_schemas()

# Seed the database with the initial admin user
seed_initial_admin()

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

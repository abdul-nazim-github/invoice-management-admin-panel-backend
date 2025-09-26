from app import create_app
from app.database.schemas.schema import create_schemas

# Create the database schema before running the app
create_schemas()

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

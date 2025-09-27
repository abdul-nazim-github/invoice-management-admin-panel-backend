from dotenv import load_dotenv
# Load environment variables from .env file before anything else
load_dotenv()

from app import create_app

# The app factory function creates the Flask application instance
app = create_app()

if __name__ == "__main__":
    # The app.run() is suitable for development.
    # For production, use a production-ready WSGI server like Gunicorn or uWSGI.
    app.run(host="0.0.0.0", port=5001, debug=True)

# =============================
# app/database/config.py
# =============================
import os
from dotenv import load_dotenv


load_dotenv()

COMMON_CONFIG={
    "autocommit": True,
    "host": os.getenv("HOST", "5000"),
}

MYSQL_CONFIG = {
"host": os.getenv("DB_HOST", "localhost"),
"user": os.getenv("DB_USER", "root"),
"password": os.getenv("DB_PASS", "root"),
"database": os.getenv("DB_NAME", "vyaper_billing_db"),
"port": int(os.getenv("DB_PORT", "3306")),
}
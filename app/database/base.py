# =============================
# app/database/base.py
# =============================
import pymysql
from app.database.config import MYSQL_CONFIG




def get_db_connection():
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        port=MYSQL_CONFIG["port"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
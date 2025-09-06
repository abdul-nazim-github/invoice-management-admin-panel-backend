import pymysql
from app.database.config import Config

def get_db_connection():
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

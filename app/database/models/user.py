from .base import get_db_connection

class User:
    @staticmethod
    def create(data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                (data['username'], data['password'], data['email'])
            )
            conn.commit()
            return User.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            return [User.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            if row:
                return User.from_row(row)
            return None

    @staticmethod
    def update(user_id, data):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET username = %s, password = %s, email = %s WHERE id = %s',
                (data['username'], data['password'], data['email'], user_id)
            )
            conn.commit()
            return User.get_by_id(user_id)

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def from_row(row):
        return {
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'email': row[3]
        }
    def to_dict(self):
      return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email
      }


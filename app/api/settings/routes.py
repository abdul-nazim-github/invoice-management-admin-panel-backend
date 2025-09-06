from . import settings_bp
from flask import jsonify, request
import mysql.connector
from config import Config
import bcrypt

def get_db_connection():
    cnx = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    return cnx

@settings_bp.route('/profile/update', methods=['PUT'])
def update_profile():
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    email = data.get('email')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    if not name and not email:
        return jsonify({'error': 'No fields to update'}), 400

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        query = "UPDATE users SET "
        params = []
        if name:
            query += "name = %s, "
            params.append(name)
        if email:
            query += "email = %s, "
            params.append(email)

        query = query.rstrip(', ') + " WHERE id = %s"
        params.append(user_id)

        cursor.execute(query, tuple(params))
        cnx.commit()

        cursor.close()
        cnx.close()
        return jsonify({'message': f'User with id {user_id} updated successfully.'})

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@settings_bp.route('/profile/password', methods=['PUT'])
def update_password():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')

    if not user_id or not password:
        return jsonify({'error': 'Missing user_id or password'}), 400

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        query = "UPDATE users SET password = %s WHERE id = %s"
        cursor.execute(query, (hashed_password, user_id))
        cnx.commit()

        cursor.close()
        cnx.close()
        return jsonify({'message': f'Password for user with id {user_id} updated successfully.'})

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@settings_bp.route('/billing', methods=['POST'])
def add_billing_details():
    data = request.get_json()
    user_id = data.get('user_id')
    address = data.get('address')
    city = data.get('city')
    state = data.get('state')
    zip_code = data.get('zip_code')
    country = data.get('country')

    if not all([user_id, address, city, state, zip_code, country]):
        return jsonify({'error': 'Missing required billing information'}), 400

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        query = "INSERT INTO billing_details (user_id, address, city, state, zip_code, country) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, address, city, state, zip_code, country))
        cnx.commit()
        billing_id = cursor.lastrowid
        cursor.close()
        cnx.close()
        return jsonify({'id': billing_id}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@settings_bp.route('/billing/<int:user_id>', methods=['PUT'])
def update_billing_details(user_id):
    data = request.get_json()
    address = data.get('address')
    city = data.get('city')
    state = data.get('state')
    zip_code = data.get('zip_code')
    country = data.get('country')

    if not any([address, city, state, zip_code, country]):
        return jsonify({'error': 'No fields to update'}), 400

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        query = "UPDATE billing_details SET "
        params = []
        if address:
            query += "address = %s, "
            params.append(address)
        if city:
            query += "city = %s, "
            params.append(city)
        if state:
            query += "state = %s, "
            params.append(state)
        if zip_code:
            query += "zip_code = %s, "
            params.append(zip_code)
        if country:
            query += "country = %s, "
            params.append(country)

        query = query.rstrip(', ') + " WHERE user_id = %s"
        params.append(user_id)

        cursor.execute(query, tuple(params))
        cnx.commit()

        cursor.close()
        cnx.close()
        return jsonify({'message': f'Billing details for user with id {user_id} updated successfully.'})

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

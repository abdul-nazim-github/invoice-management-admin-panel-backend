from . import billing_bp
from flask import jsonify, request
import mysql.connector
from config import Config

def get_db_connection():
    cnx = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    return cnx

@billing_bp.route('/', methods=['POST'])
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

@billing_bp.route('/<int:user_id>', methods=['PUT'])
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

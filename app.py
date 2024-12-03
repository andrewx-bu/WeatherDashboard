import os
from flask import Flask, request, make_response, jsonify
import requests
import sqlite3
from dotenv import load_dotenv
from helpers import convert_wind_deg_to_direction
import logging

# Load env variables
load_dotenv()

# Set up logging to a file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Flask app initialization
app = Flask(__name__)

# Connect to db
def get_db_connection():
    """
    Establish connection to SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object.

    Raises:
        sqlite3.DatabaseError: If there is an issue with the database connection.
    """
    try:
        conn = sqlite3.connect('weather.db')
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

# Route to add a favorite location
@app.route('/api/add-favorite', methods=['POST'])
def add_favorite():
    """
    POST: Adds a user's favorite location to the database.

    Expected JSON Input:
        - user_id (str): The ID of the user adding the favorite location.
        - location (str): The name of the location to be saved as a favorite.

    Returns:
        Response: JSON response with status and message.

    Raises:
        400 error if missing input.
        500 error if there is an issue adding the favorite to the database.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        location = data.get('location')

        # Validate input
        if not user_id or not location:
            logging.warning("user_id or location missing in request.")
            return make_response(jsonify({'error': 'user_id and location are required'}), 400)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the favorite location into the favorites table
        cursor.execute('''
            INSERT INTO favorites (user_id, location)
            VALUES (?, ?)
        ''', (user_id, location))

        conn.commit()
        conn.close()

        logging.info(f"Favorite location '{location}' added for user {user_id}.")
        return make_response(jsonify({'status': 'success', 'message': 'Favorite location added'}), 201)

    except Exception as e:
        logging.error(f"Error adding favorite: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to get all favorites for a user
@app.route('/api/get-favorites', methods=['GET'])
def get_favorites():
    """
    GET: Retrieves all favorite locations for a given user.

    Query Parameter:
        - user_id (str): The ID of the user whose favorites are being request

    Returns:
        Response: JSON response with a list of favorite locations.
    
    Raises:
        400 error if missing input.
        500 error if there is an issue fetching favorites
    """
    try:
        user_id = request.args.get('user_id')

        # Validate input
        if not user_id:
            logging.warning("user_id missing in request.")
            return make_response(jsonify({'error': 'user_id is required'}), 400)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get all favorites for the user
        cursor.execute('SELECT id, location FROM favorites WHERE user_id = ?', (user_id,))
        favorites = cursor.fetchall()

        conn.close()

        if not favorites:
            return make_response(jsonify({'message': 'No favorites found'}), 404)

        # Prepare the response data
        favorite_locations = [{'id': fav[0], 'location': fav[1]} for fav in favorites]

        logging.info(f"Fetched {len(favorite_locations)} favorites for user {user_id}.")
        return make_response(jsonify({'favorites': favorite_locations}), 200)

    except Exception as e:
        logging.error(f"Error fetching favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

if __name__ == '__main__':
    app.run(debug=True)
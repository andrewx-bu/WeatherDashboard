import os
from flask import Flask, request, make_response, jsonify
import requests
import urllib3
import sqlite3
from dotenv import load_dotenv
from openweather_api import get_coords, get_forecast, get_current_weather
import logging
import bcrypt

# Load env variables
load_dotenv()

# Set up logging to a file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# prevent debug logs from being shown
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

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

#############################
#                           #
#      Health Checks        #
#                           #
#############################

# Route to check health
@app.route('/api/health', methods=['GET'])
def healthcheck():
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    app.logger.info('Health check')
    return make_response(jsonify({'status': 'healthy'}), 200)

# Route to check databse health
@app.route('/api/db-check', methods=['GET'])
def db_check():
    """
    Route to check if the database connection and songs table are functional.

    Returns:
        JSON response indicating the database health status.
    Raises:
        404 error if there is an issue with the database.
    """
    try:
        conn = get_db_connection()
        conn.close()
        app.logger.info("Database connection is OK.")
        return make_response(jsonify({'database_status': 'healthy'}), 200)
    except Exception as e:
        logging.error(f"Database check failed: {e}")
        return make_response(jsonify({'error': str(e)}), 404)

#############################
#                           #
#   Favorites  Management   #
#                           #
#############################

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
        400 error if missing input, or location already exists for that user.
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

        # Check if the location already exists for the user
        cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))
        existing_favorite = cursor.fetchone()

        if existing_favorite:
            logging.warning(f"Favorite location '{location}' already exists for user {user_id}.")
            return make_response(jsonify({'error': f"'{location}' is already a favorite location for this user."}), 400)

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

# Route to remove a favorite location for a user
@app.route('/api/remove-favorite', methods=['DELETE'])
def remove_favorite():
    """
    DELETE: Removes a user's favorite location from the database.

    Expected JSON Input:
        - user_id (str): The ID of the user removing the favorite location.
        - location (str): The name of the location to be removed from favorites.

    Returns:
        Response: JSON response with status and message.

    Raises:
        400 error if missing input or location not found.
        500 error if there is an issue removing the favorite from the database.
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

        # Check if the location exists for the user
        cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))
        favorite = cursor.fetchone()

        if not favorite:
            logging.warning(f"Favorite location '{location}' not found for user {user_id}.")
            return make_response(jsonify({'error': f"'{location}' is not a favorite location for this user."}), 400)

        # Remove the favorite location from the database
        cursor.execute('DELETE FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))

        conn.commit()
        conn.close()

        logging.info(f"Favorite location '{location}' removed for user {user_id}.")
        return make_response(jsonify({'status': 'success', 'message': 'Favorite location removed'}), 200)

    except Exception as e:
        logging.error(f"Error removing favorite: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to update a favorite for a user
@app.route('/api/update-favorite', methods=['PUT'])
def update_favorite():
    """
    PUT: Updates a user's favorite location in the database.

    Expected JSON Input:
        - user_id (str): The ID of the user updating the favorite location.
        - old_location (str): The current name of the location to be updated.
        - new_location (str): The new name of the location to replace the old one.

    Returns:
        Response: JSON response with status and message.

    Raises:
        400 error if missing input.
        404 error if the old location does not exist for the user.
        500 error if there is an issue updating the favorite location in the database.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        old_location = data.get('old_location')
        new_location = data.get('new_location')

        if not user_id or not old_location or not new_location:
            logging.warning("Missing user_id, old_location, or new_location.")
            return make_response(jsonify({'error': 'user_id, old_location, and new_location are required'}), 400)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the favorite location
        cursor.execute(
            '''UPDATE favorites SET location = ? WHERE user_id = ? AND location = ?''', 
            (new_location, user_id, old_location)
        )

        if cursor.rowcount == 0:
            # No rows updated, meaning old_location does not exist
            conn.close()
            logging.warning(f"Favorite location '{old_location}' not found for user {user_id}.")
            return make_response(jsonify({'error': f"'{old_location}' is not a favorite location for this user."}), 404)
        
        conn.commit()
        conn.close()

        logging.info(f"Favorite location '{old_location}' updated to '{new_location}' for user {user_id}.")
        return make_response(jsonify({'status': 'success', 'message': f"'{old_location}' updated to '{new_location}'"}), 200)

    except Exception as e:
        logging.error(f"Error updating favorite: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to clear all favorites for a user
@app.route('/api/clear-favorites', methods=['DELETE'])
def clear_favorites():
    """
    POST: Removes all favorite locations from from the database.

    Expected JSON Input:
        - user_id (str): The ID of the user whose favorite locations are to be removed.

    Returns:
        Response: JSON response with status and message.

    Raises:
        400 error if missing input.
        500 error if there is an issue removing the favorites from the database.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            logging.warning("user_id missing in request.")
            return make_response(jsonify({'error': 'user_id is required'}), 400)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        logging.info(f"All favorite locations removed for user {user_id}.")
        return make_response(jsonify({'status': 'success', 'message': 'All favorite locations removed'}), 200)

    except Exception as e:
        logging.error(f"Error clearing favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to get all favorites for a user
@app.route('/api/get-favorites', methods=['GET'])
def get_favorites():
    """
    GET: Retrieves all favorite locations for a given user.

    Query Parameters:
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

#############################
#                           #
#         API Calls         #
#                           #
#############################

# Route to get coordinates of a city
@app.route('/api/coords', methods=['GET'])
def coords():
    """
    GET: Fetch coordinates for a city.

    Query Parameters:
        - city (str): Name of the city.
        - country_code (str, optional): Country code.

    Returns:
        Response: JSON response containing latitude and longitude.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)

    if not city:
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if coords:
        return make_response(jsonify({'coordinates': coords}), 200)
    else:
        return make_response(jsonify({'error': 'Could not fetch coordinates'}), 500)

# Route to get weather forecast for a city
@app.route('/api/forecast', methods=['GET'])
def forecast():
    """
    GET: Fetch weather forecast for a city.

    Query Parameters:
        - city (str): The name of the city.
        - country_code (str, optional): Country code.
        - units (str, optional): Units of measurement (standard, metric, imperial). Defaults to "imperial".

    Returns:
        Response: JSON response containing weather forecast.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)
    units = request.args.get('units', 'imperial')

    logging.info(f"Forecast request received for city: {city}, country_code: {country_code}, units: {units}")

    if not city:
        logging.warning("Missing 'city' parameter in forecast request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logging.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logging.info(f"Coordinates for city {city}: {coords}")

    forecast_data = get_forecast(coords['lat'], coords['lon'], units)
    if forecast_data:
        logging.info(f"Successfully fetched forecast data for city: {city}")
        return make_response(jsonify(forecast_data), 200)
    else:
        logging.error(f"Failed to fetch forecast data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch forecast data'}), 500)

# Route to get current weather for a city
@app.route('/api/weather', methods=['GET'])
def current_weather():
    """
    GET: Fetch current weather for a city.

    Query Parameters:
        - city (str): Name of the city.
        - country_code (str, optional): Country code.
        - units (str, optional): Units of measurement (standard, metric, imperial). Defaults to "imperial".

    Returns:
        Response: JSON response containing current weather data.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)
    units = request.args.get('units', 'imperial')

    logging.info(f"Current weather request received for city: {city}, country_code: {country_code}, units: {units}")

    if not city:
        logging.warning("Missing 'city' parameter in current weather request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logging.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logging.info(f"Coordinates for city {city}: {coords}")

    weather_data = get_current_weather(coords['lat'], coords['lon'], units)
    if weather_data:
        logging.info(f"Successfully fetched current weather data for city: {city}")
        return make_response(jsonify(weather_data), 200)
    else:
        logging.error(f"Failed to fetch current weather data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch current weather data'}), 500)

#############################
#                           #
#         Passwords         #
#                           #
#############################

@app.route('/create-account', methods=['POST'])
def create_account():
    """
    POST: Allows a user to create an account with a username and password.

    Expected JSON Input:
        - username (str): The username for the new account.
        - password (str): The password for the new account.

    Returns:
        Response: JSON response with status and a success or error message.

    Raises:
        400 error if the username or password is missing, or the username is already taken.
        500 error if there is an issue with the database operation.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_response(jsonify({'error': 'Username and password are required'}), 400)

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)',
            (username, salt.decode(), password_hash.decode())
        )
        conn.commit()
        conn.close()

        return make_response(jsonify({'status': 'success', 'message': 'Account created'}), 201)

    except sqlite3.IntegrityError:
        return make_response(jsonify({'error': 'Username already exists'}), 400)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/login', methods=['GET'])
def login():
    """
    GET: Authenticates a user by verifying the provided password with the stored hash.

    Query Parameters:
        - username (str): The username of the account.
        - password (str): The password to verify.

    Returns:
        Response: JSON response indicating success or failure of login.

    Raises:
        400 error if the username or password is missing.
        404 error if the username does not exist.
        401 error if the password is incorrect.
        500 error if there is an issue with the database operation.
    """
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return make_response(jsonify({'error': 'Username and password are required'}), 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT salt, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return make_response(jsonify({'error': 'Invalid username or password'}), 404)

        salt, stored_hash = user
        if bcrypt.hashpw(password.encode('utf-8'), stored_hash.encode()) == stored_hash.encode():
            return make_response(jsonify({'status': 'success', 'message': 'Login successful'}), 200)
        else:
            return make_response(jsonify({'error': 'Invalid username or password'}), 401)

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/update-password', methods=['PUT'])
def update_password():
    """
    PUT: Updates the password for an existing user account.

    Expected JSON Input:
        - username (str): The username of the account.
        - old_password (str): The current password for the account.
        - new_password (str): The new password to replace the old one.

    Returns:
        Response: JSON response with status and a success or error message.

    Raises:
        400 error if the username, old password, or new password is missing.
        401 error if the old password is incorrect.
        404 error if the username does not exist.
        500 error if there is an issue with the database operation.
    """
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not username or not old_password or not new_password:
        return make_response(jsonify({'error': 'Username, old password, and new password are required'}), 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT salt, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()

        if not user:
            return make_response(jsonify({'error': 'Invalid username or password'}), 404)

        salt, stored_hash = user

        if bcrypt.hashpw(old_password.encode('utf-8'), stored_hash.encode()) != stored_hash.encode():
            return make_response(jsonify({'error': 'Old password is incorrect'}), 401)

        new_salt = bcrypt.gensalt()
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), new_salt)

        cursor.execute(
            'UPDATE users SET salt = ?, password_hash = ? WHERE username = ?',
            (new_salt.decode(), new_hash.decode(), username)
        )
        conn.commit()
        conn.close()

        return make_response(jsonify({'status': 'success', 'message': 'Password updated'}), 200)

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)


if __name__ == '__main__':
    app.run(debug=True)
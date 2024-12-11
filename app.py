import sqlite3
from flask import Flask, request, make_response, jsonify
from dotenv import load_dotenv
from models.UserModel import UserModel
from models.FavoriteModel import FavoriteModel
from openweather_api import get_coords, get_forecast, get_air_pollution_forecast ,get_current_weather, get_air_pollution
from utils.logger import setup_logger
from utils.sql import get_db_connection

load_dotenv()
logger = setup_logger()

# Flask app initialization
app = Flask(__name__)

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
    logger.info('Health check')
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
        logger.info("Database connection is OK.")
        return make_response(jsonify({'database_status': 'healthy'}), 200)
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return make_response(jsonify({'error': str(e)}), 404)

#############################
#                           #
#  User Account Management  #
#                           #
#############################

# Route to create a new account
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
        logger.warning("Create account request missing username or password.")
        return make_response(jsonify({'error': 'Username and password are required'}), 400)

    if not UserModel.check_password_validity(password):
        logger.warning("Password does not meet complexity requirements.")
        return make_response(jsonify({'error': 'Password must be between 8 and 20 characters long, contain at least one letter and one digit.'}), 400)

    if UserModel.is_username_taken(username):
        logger.warning(f"Username {username} is already taken.")
        return make_response(jsonify({'error': 'Username is already taken'}), 400)
    
    try:
        UserModel.create_user(username, password)
        logger.info(f"Account created for username: {username}")
        return make_response(jsonify({'status': 'success', 'message': 'Account created'}), 201)
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to delete an existing account
@app.route('/delete-account', methods=['DELETE'])
def delete_account():
    """
    DELETE: Deletes a user account and all its favorites from the database.

    Expected JSON Input:
        - username (str): The username of the account to delete.
        - password (str): The password of the account.

    Returns:
        Response: JSON response indicating success or failure.

    Raises:
        400 error if username or password is missing.
        401 error if password is incorrect.
        404 error if the user does not exist.
        500 error if there is an issue with the database operation.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_response(jsonify({'error': 'Username and password are required'}), 400)

    try:
        # Check if the user exists and password is correct before deletion
        if not UserModel.authenticate_user(username, password):
            return make_response(jsonify({'error': 'Incorrect password or user not found'}), 401)
        UserModel.delete_user(username)
        logger.info(f"Account deleted for username: {username}")
        return make_response(jsonify({'status': 'success', 'message': 'Account deleted'}), 200)
    
    except Exception as e:
        logger.error(f"Account deletion failed: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to login to an account
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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logger.warning("Login request missing username or password.")
        return make_response(jsonify({'error': 'Username and password are required'}), 400)

    try:
        is_authenticated = UserModel.authenticate_user(username, password)
        if is_authenticated:
            logger.info(f"User '{username}' logged in successfully.")
            return make_response(jsonify({'status': 'success', 'message': 'Login successful'}), 200)
        else:
            logger.warning(f"Login failed for user '{username}': Incorrect password.")
            return make_response(jsonify({'error': 'Invalid username or password'}), 401)
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to update password for an account
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
        logger.warning("Update password request missing parameters.")
        return make_response(jsonify({'error': 'Username, old password, and new password are required'}), 400)

    if not UserModel.check_password_validity(new_password):
        logger.warning("New password does not meet complexity requirements.")
        return make_response(jsonify({'error': 'New password must be between 8 and 20 characters long, contain at least one letter and one digit.'}), 400)
    
    try:
        # Check if old password is correct
        if not UserModel.authenticate_user(username, old_password):
            return make_response(jsonify({'error': 'Old password is incorrect'}), 401)

        UserModel.update_password(username, new_password)
        logger.info(f"Password updated for user '{username}'.")
        return make_response(jsonify({'status': 'success', 'message': 'Password updated'}), 200)
    except Exception as e:
        logger.error(f"Password update failed: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

# Route to get all accounts/users
@app.route('/get-all-users', methods=['GET'])
def get_all_users():
    """
    GET: Retrieves a list of all users in the database.
    
    Returns:
        Response: JSON response with a list of all users.
    
    Raises:
        500 error if there is an issue fetching the users.
    """
    try:
        users = UserModel.get_all_users()
        if users:
            return make_response(jsonify({'users': users}), 200)
        else:
            return make_response(jsonify({'message': 'No users found'}), 404)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

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

        if not user_id or not location:
            logger.warning("user_id or location missing in request.")
            return make_response(jsonify({'error': 'user_id and location are required'}), 400)

        try:
            FavoriteModel.add_favorite(user_id, location)
            logger.info(f"Favorite location '{location}' added for user {user_id}.")
            return make_response(jsonify({'status': 'success', 'message': 'Favorite location added'}), 201)
        except ValueError as e:
            logger.warning(f"Error adding favorite for user {user_id}: {e}")
            return make_response(jsonify({'error': str(e)}), 400)
        
    except sqlite3.IntegrityError as e:
        # Catch foreign key violation
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify({'error': 'User ID does not exist'}), 400
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
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

        if not user_id or not location:
            logger.warning("Missing user_id or location in request.")
            return make_response(jsonify({'error': 'user_id and location are required'}), 400)

        try:
            FavoriteModel.remove_favorite(user_id, location)
            logger.info(f"Favorite location '{location}' removed for user {user_id}.")
            return make_response(jsonify({'status': 'success', 'message': 'Favorite location removed'}), 200)
        except ValueError as e:
            logger.warning(f"Error removing favorite for user {user_id}: {e}")
            return make_response(jsonify({'error': str(e)}), 400)

    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
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
        409 error if the new location already exists as a favorite.
        500 error if there is an issue updating the favorite location in the database.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        old_location = data.get('old_location')
        new_location = data.get('new_location')

        if not user_id or not old_location or not new_location:
            logger.warning("Missing user_id, old_location, or new_location in request.")
            return make_response(jsonify({'error': 'user_id, old_location, and new_location are required'}), 400)

        try:
            FavoriteModel.update_favorite(user_id, old_location, new_location)
            logger.info(f"Favorite location updated from '{old_location}' to '{new_location}' for user {user_id}.")
            return make_response(jsonify({'status': 'success', 'message': f"'{old_location}' updated to '{new_location}'"}), 200)
        except ValueError as e:
            logger.warning(f"Error updating favorite for user {user_id}: {e}")
            return make_response(jsonify({'error': str(e)}), 400)

    except Exception as e:
        logger.error(f"Error updating favorite: {e}")
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
            logger.warning("Missing user_id in request.")
            return make_response(jsonify({'error': 'user_id is required'}), 400)

        try:
            FavoriteModel.clear_favorites(user_id)
            logger.info(f"All favorites cleared for user {user_id}.")
            return make_response(jsonify({'status': 'success', 'message': 'All favorite locations removed'}), 200)
        except Exception as e:
            logger.error(f"Error clearing favorites for user {user_id}: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    except Exception as e:
        logger.error(f"Error clearing favorites: {e}")
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

        if not user_id:
            logger.warning("Missing user_id in request.")
            return make_response(jsonify({'error': 'user_id is required'}), 400)

        try:
            favorites = FavoriteModel.get_favorites(user_id)
            if not favorites:
                return make_response(jsonify({'message': 'No favorites found'}), 404)

            favorite_locations = [
                {'id': fav[0], 'location': fav[1], 'created_at': fav[2], 'updated_at': fav[3]} for fav in favorites
            ]
            logger.info(f"Returning {len(favorites)} favorites for user {user_id}.")
            return make_response(jsonify({'favorites': favorite_locations}), 200)
        except Exception as e:
            logger.error(f"Error fetching favorites for user {user_id}: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    except Exception as e:
        logger.error(f"Error fetching favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

#############################
#                           #
#        API Routes         #
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
    
    Raises:
        400 error if 'city' is missing in the request.
        500 error if there is an issue fetching coordinates.
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

    Raises:
        400 error if 'city' is missing in the request.
        500 error if there is an issue fetching coordinates or forecast data.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)
    units = request.args.get('units', 'imperial')

    logger.info(f"Forecast request received for city: {city}, country_code: {country_code}, units: {units}")

    if not city:
        logger.warning("Missing 'city' parameter in forecast request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logger.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logger.info(f"Coordinates for city {city}: {coords}")

    forecast_data = get_forecast(coords['lat'], coords['lon'], units)
    if forecast_data:
        logger.info(f"Successfully fetched forecast data for city: {city}")
        return make_response(jsonify(forecast_data), 200)
    else:
        logger.error(f"Failed to fetch forecast data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch forecast data'}), 500)

# Route to get air pollution forecast data for a city
@app.route('/api/air-pollution-forecast', methods=['GET'])
def air_pollution_forecast():
    """
    GET: Fetch air pollution forecast data for a city.

    Query Parameters:
        - city (str): Name of the city.
        - country_code (str, optional): Country code.

    Returns:
        Response: JSON response containing air pollution forecast data.
    
    Raises:
        400 error if 'city' is missing in the request.
        500 error if there is an issue fetching coordinates or pollution forecast data.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)

    logger.info(f"Air pollution forecast request received for city: {city}, country_code: {country_code}")

    if not city:
        logger.warning("Missing 'city' parameter in air pollution forecast request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logger.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logger.info(f"Coordinates for city {city}: {coords}")

    pollution_forecast_data = get_air_pollution_forecast(coords['lat'], coords['lon'])
    if pollution_forecast_data:
        logger.info(f"Successfully fetched air pollution forecast data for city: {city}")
        return make_response(jsonify(pollution_forecast_data), 200)
    else:
        logger.error(f"Failed to fetch air pollution forecast data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch air pollution forecast data'}), 500)

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
    
    Raises:
        400 error if 'city' is missing in the request.
        500 error if there is an issue fetching coordinates or current weather data.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)
    units = request.args.get('units', 'imperial')

    logger.info(f"Current weather request received for city: {city}, country_code: {country_code}, units: {units}")

    if not city:
        logger.warning("Missing 'city' parameter in current weather request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logger.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logger.info(f"Coordinates for city {city}: {coords}")

    weather_data = get_current_weather(coords['lat'], coords['lon'], units)
    if weather_data:
        logger.info(f"Successfully fetched current weather data for city: {city}")
        return make_response(jsonify(weather_data), 200)
    else:
        logger.error(f"Failed to fetch current weather data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch current weather data'}), 500)

# Route to get air pollution data for a city
@app.route('/api/air-pollution', methods=['GET'])
def air_pollution():
    """
    GET: Fetch air pollution data for a city.

    Query Parameters:
        - city (str): Name of the city.
        - country_code (str, optional): Country code.

    Returns:
        Response: JSON response containing air pollution data.
    
    Raises:
        400 error if 'city' is missing in the request.
        500 error if there is an issue fetching coordinates or air pollution data.
    """
    city = request.args.get('city')
    country_code = request.args.get('country_code', None)

    logger.info(f"Air pollution request received for city: {city}, country_code: {country_code}")

    if not city:
        logger.warning("Missing 'city' parameter in air pollution request.")
        return make_response(jsonify({'error': 'City is required'}), 400)

    coords = get_coords(city, country_code)
    if not coords:
        logger.error(f"Failed to fetch coordinates for city: {city}, country_code: {country_code}")
        return make_response(jsonify({'error': 'Could not fetch coordinates for the city'}), 500)

    logger.info(f"Coordinates for city {city}: {coords}")

    pollution_data = get_air_pollution(coords['lat'], coords['lon'])
    if pollution_data:
        logger.info(f"Successfully fetched air pollution data for city: {city}")
        return make_response(jsonify(pollution_data), 200)
    else:
        logger.error(f"Failed to fetch air pollution data for city: {city}, coordinates: {coords}")
        return make_response(jsonify({'error': 'Could not fetch air pollution data'}), 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
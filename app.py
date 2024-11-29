import os
from flask import Flask, render_template, request, make_response, jsonify
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
    """
    conn = sqlite3.connect('weather.db')
    conn.row_factory = sqlite3.Row  # Access rows as dictionaries
    return conn

@app.route('/')
def index():
    """
    Route to render homepage.

    Returns:
        Rendered HTML homepage.
    """
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    """
    Route to fetch weather data for a specified city

    Returns:
        Rendered HTML page with weather data or error message.

    Raises:
        500 error if there is an issue fetching current weather.
    """
    city = request.form['city']
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"

    try:
        app.logger.info(f"Fetching weather data for city: {city}")
        
        # Make the API request
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            app.logger.info(f"Weather data retrieved for city: {city}")

            # Extract relevant data from the API response
            temperature = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            wind_deg = data['wind']['deg']
            wind_direction = convert_wind_deg_to_direction(wind_deg)
            app.logger.info(f"Inserting weather data for {city}: Temp={temperature}, Feels like={feels_like}, Wind Speed={wind_speed}, Direction={wind_direction}")

            # Save the weather data into the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO weather_log (city, temperature, feels_like, humidity, wind_speed, wind_direction) VALUES (?, ?, ?, ?, ?, ?)",
                           (city, temperature, feels_like, humidity, wind_speed, wind_direction))
            conn.commit()
            conn.close()
            app.logger.info(f"Weather data for {city} saved successfully")

            # Return the weather data to the HTML page for rendering
            return render_template('weather.html', weather=data, feels_like=feels_like, humidity=humidity, wind_speed=wind_speed, wind_direction=wind_direction)
        
        else:
            # Handle API error (e.g., invalid city)
            app.logger.warning(f"City not found: {city}")
            error_message = "The city you entered was not found. Please try again."
            return render_template('weather.html', weather=None, error_message=error_message)
    except Exception as e:
        # Handle general API request errors
        app.logger.error(f"Error fetching weather data: {str(e)}")
        return make_response(jsonify({'error': 'Error fetching weather data'}), 500)
    
@app.route('/logs')
def logs():
    """
    Route to display weather logs from the database.

    Returns:
        Rendered HTML page with the weather logs.

    Raises:
        500 error if there is an issue fetching logs.
    """
    try:
        app.logger.info("Fetching weather logs")

        # Retrieve weather logs from the database
        conn = get_db_connection()
        logs = conn.execute('SELECT * FROM weather_log ORDER BY timestamp DESC').fetchall()
        conn.close()

        app.logger.info("Successfully fetched weather logs")

        # Render logs in the template
        return render_template('logs.html', logs=logs)

    except Exception as e:
        # Handle general database or query errors
        app.logger.error(f"Error fetching weather logs: {str(e)}")
        return make_response(jsonify({'error': 'Error fetching weather logs'}), 500)# Shows logs ordered by most recent entries

if __name__ == '__main__':
    app.run(debug=True)
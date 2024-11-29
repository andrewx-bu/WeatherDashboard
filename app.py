import os
from flask import Flask, render_template, request
import requests
import sqlite3
from dotenv import load_dotenv
from helpers import convert_wind_deg_to_direction

load_dotenv()

app = Flask(__name__)

# Connect to db
def get_db_connection():
    conn = sqlite3.connect('weather.db')
    conn.row_factory = sqlite3.Row  # Access rows as dictionaries
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form['city']
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        # Save weather data
        temperature = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        wind_deg = data['wind']['deg']
        wind_direction = convert_wind_deg_to_direction(wind_deg)

        # Add weather data to database
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO weather_log (city, temperature, feels_like, humidity, wind_speed, wind_direction) VALUES (?, ?, ?, ?, ?, ?)",
                        (city, temperature, feels_like, humidity, wind_speed, wind_direction))
        conn.commit()
        conn.close()

        # Return weather data to template
        return render_template('weather.html', weather=data, feels_like=feels_like, humidity=humidity, wind_speed=wind_speed, wind_direction=wind_direction)
    else:
        # Invalid city error (status code 404)
        error_message = "The city you entered was not found. Please try again."
        return render_template('weather.html', weather=None, error_message=error_message)
    
@app.route('/logs')
def logs():
    # Shows logs ordered by most recent entries
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM weather_log ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
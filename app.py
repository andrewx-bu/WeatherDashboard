import os
from flask import Flask, render_template, request
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('weather.db')
    conn.row_factory = sqlite3.Row  # Access rows as dictionaries
    return conn

def convert_wind_deg_to_direction(deg):
    if deg >= 337.5 or deg < 22.5:
        return "N"
    elif 22.5 <= deg < 67.5:
        return "NE"
    elif 67.5 <= deg < 112.5:
        return "E"
    elif 112.5 <= deg < 157.5:
        return "SE"
    elif 157.5 <= deg < 202.5:
        return "S"
    elif 202.5 <= deg < 247.5:
        return "SW"
    elif 247.5 <= deg < 292.5:
        return "W"
    elif 292.5 <= deg < 337.5:
        return "NW"
    else:
        return "?"

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
        temperature = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        wind_deg = data['wind']['deg']
        wind_direction = convert_wind_deg_to_direction(wind_deg)

        # Save to the database (optional, you can choose to save these additional values)
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO weather_log (city, temperature, feels_like, humidity, wind_speed, wind_direction) VALUES (?, ?, ?, ?, ?, ?)",
                       (city, temperature, feels_like, humidity, wind_speed, wind_direction))
        conn.commit()
        conn.close()

        return render_template('weather.html', weather=data, feels_like=feels_like, humidity=humidity, wind_speed=wind_speed, wind_direction=wind_direction)
    else:
        error_message = "City not found or error fetching weather data"
        return render_template('weather.html', error_message=error_message)

@app.route('/logs')
def logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM weather_log ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
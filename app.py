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

    # Save data to the database if successful
    if response.status_code == 200:
        conn = get_db_connection()
        conn.execute('INSERT INTO weather_log (city, temperature) VALUES (?, ?)',
                     (data['name'], data['main']['temp']))
        conn.commit()
        conn.close()

    return render_template('weather.html', weather=data)

@app.route('/logs')
def logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM weather_log ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
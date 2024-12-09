# All calls to OpenWeatherAPI are made here

import os
import requests
import urllib3
from dotenv import load_dotenv
import logging

load_dotenv()
API_KEY = os.getenv('OPENWEATHER_API_KEY')

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Function to get coordinates (lat, lon) by city name
def get_coords(city: str, country_code: str = None):
    """
    Fetches the coordinates (latitude, longitude) of a city.

    Args:
        city (str): The name of the city.
        country_code (str, optional): The country code. Defaults to None.

    Returns:
        dict: A dictionary containing the latitude and longitude of the city.
    """
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}"
    
    if country_code:
        url += f",{country_code}"
    
    url += f"&appid={API_KEY}"

    response = requests.get(url)
    
    try:
        response = requests.get(url)
        data = response.json()
        if data:
            logging.info(f"Found coordinates: {data[0]['lat']}, {data[0]['lon']}")
            return data[0]
        else:
            logging.warning(f"No data found for {city}.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
    return None

# Function to get weather forecast
def get_forecast(lat: float, lon: float, units: str = "imperial"):
    """
    Fetches weather forecast.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        units (str): Units of measurement (standard, metric, imperial). Defaults to "imperial".

    Returns:
        dict: A dictionary containing forecast data.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "units": units,
        "appid": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        logging.info(f"Forecast data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching forecast: {e}")
        return None

# Function to get current weather
def get_current_weather(lat: float, lon: float, units: str = "imperial"):
    """
    Fetches current weather.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        units (str): Units of measurement (standard, metric, imperial). Defaults to "imperial".

    Returns:
        dict: A dictionary containing current weather data.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "units": units,
        "appid": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        logging.info(f"Current weather data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching current weather: {e}")
        return None
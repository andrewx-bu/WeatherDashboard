# All calls to OpenWeatherAPI are made here

import os
import requests
from dotenv import load_dotenv
from utils.logger import setup_logger

load_dotenv()
API_KEY = os.getenv('OPENWEATHER_API_KEY')
logger = setup_logger()

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
            logger.info(f"Found coordinates: {data[0]['lat']}, {data[0]['lon']}")
            return data[0]
        else:
            logger.warning(f"No data found for {city}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
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
        logger.info(f"Forecast data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching forecast: {e}")
        return None

# Function to get air pollution forecast data
def get_air_pollution_forecast(lat: float, lon: float):
    """
    Fetches air pollution forecast data for a location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        dict: A dictionary containing air pollution forecast data.
    """
    url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        logger.info(f"Air pollution forecast data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching air pollution forecast data: {e}")
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
        logger.info(f"Current weather data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching current weather: {e}")
        return None

# Function to get air pollution
def get_air_pollution(lat: float, lon: float):
    """
    Fetches air pollution data for a location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        dict: A dictionary containing air pollution data.
    """
    url = f"http://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        logger.info(f"Air pollution data retrieved for lat={lat}, lon={lon}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching air pollution data: {e}")
        return None
# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Weather parameters
PARAMETERS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "rain_sum",
    "snowfall_sum",
    "sunshine_duration"
]

# Folder for CSVs
OUTPUT_DIR = "data"

# MySQL connection config - Now using environment variables
MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "weather_user"),
    "password": os.getenv("DB_PASSWORD", ""),  # Empty default forces env variable
    "database": os.getenv("DB_NAME", "weather_db"),
    "port": int(os.getenv("DB_PORT", "3306"))
}
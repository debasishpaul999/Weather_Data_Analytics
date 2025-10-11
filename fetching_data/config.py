# config.py

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

# Default output directory
OUTPUT_DIR = "data"

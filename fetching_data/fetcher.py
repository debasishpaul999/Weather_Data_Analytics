# fetcher.py
import requests
import config

def get_coordinates(place_name):
    """Fetch latitude and longitude for a given place name using Open-Meteo Geocoding API."""
    url = config.GEOCODE_URL
    params = {"name": place_name, "count": 1}
    response = requests.get(url, params=params)
    response.raise_for_status()

    results = response.json().get("results")
    if not results:
        raise ValueError(f"No location found for '{place_name}'.")

    location = results[0]
    return location["latitude"], location["longitude"], location["name"], location.get("country", "")


def fetch_weather_data(lat, lon, start_date, end_date, params):
    """Fetch daily weather data from Open-Meteo API."""
    url = config.API_URL
    payload = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(params),
        "timezone": "auto"
    }

    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()
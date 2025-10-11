# main.py
from fetcher import get_coordinates, fetch_weather_data
from processor import process_and_save
import config
import os

def main():
    print("🌦️ Weather Data Collector using Open-Meteo API")
    print("--------------------------------------------------")

    # User input
    place = input("Enter location name (e.g., New Delhi): ").strip()
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    print(f"\n📍 Searching for '{place}'...")
    try:
        lat, lon, city_name, country = get_coordinates(place)
        print(f"✅ Found: {city_name}, {country} ({lat}, {lon})")

        print(f"📅 Date Range: {start_date} → {end_date}")
        print("Fetching weather data...")

        data = fetch_weather_data(
            lat, lon, start_date, end_date, config.PARAMETERS
        )

        # Save to city-specific folder
        folder = os.path.join(config.OUTPUT_DIR, city_name.replace(" ", "_"))
        filename = f"weather_data_{start_date}_to_{end_date}.csv"
        process_and_save(data, folder, filename)

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"✅ Process complete. Files saved in '{config.OUTPUT_DIR}'.")

if __name__ == "__main__":
    main()

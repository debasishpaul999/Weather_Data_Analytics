# main.py
from fetcher import get_coordinates, fetch_weather_data
from processor import process_and_save
import config
import os
from datetime import datetime

def main():
    print("🌦️ Weather Data Collector (Year-wise CSVs)")
    print("--------------------------------------------------")

    # User input
    place = input("Enter location name (e.g., New Delhi): ").strip()
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    # Convert to datetime
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Get coordinates
    print(f"\n📍 Searching for '{place}'...")
    try:
        lat, lon, city_name, country = get_coordinates(place)
        print(f"✅ Found: {city_name}, {country} ({lat}, {lon})")
    except Exception as e:
        print(f"❌ Error finding location: {e}")
        return

    # Create city folder
    folder = os.path.join(config.OUTPUT_DIR, city_name.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    # Loop year by year
    current_year = start.year
    while current_year <= end.year:
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31)

        # Adjust start and end dates if range is partial
        if current_year == start.year:
            year_start = start
        if current_year == end.year:
            year_end = end

        print(f"\n📅 Fetching data for {current_year}...")
        try:
            data = fetch_weather_data(
                lat, lon,
                year_start.strftime("%Y-%m-%d"),
                year_end.strftime("%Y-%m-%d"),
                config.PARAMETERS
            )

            filename = f"weather_data_{current_year}.csv"
            process_and_save(data, folder, filename)
        except Exception as e:
            print(f"❌ Error fetching data for {current_year}: {e}")

        current_year += 1

    print(f"\n✅ All yearly data saved in '{folder}'.")

if __name__ == "__main__":
    main()

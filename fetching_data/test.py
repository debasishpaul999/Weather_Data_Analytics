# test.py
from fetcher import get_coordinates, fetch_weather_data
from processor import process_to_database
from database import create_connection, create_main_table, has_complete_year_data, export_requested_data_to_csv
import config
import os
from datetime import datetime

def main():
    print("🌦️ Smart Weather Data Collector - Complete Year Strategy")
    print("--------------------------------------------------------")

    place = input("Enter location name (e.g., Mumbai): ").strip()
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    print(f"\n📍 Searching for '{place}'...")
    try:
        lat, lon, city_name, country = get_coordinates(place)
        print(f"✅ Found: {city_name}, {country} ({lat}, {lon})")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Create folder structure
    folder = os.path.join(config.OUTPUT_DIR, city_name.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    # Database setup
    conn = create_connection()
    create_main_table(conn)

    # Strategy: Always fetch and store COMPLETE years
    start_year = start.year
    end_year = end.year
    
    print(f"\n📦 Building complete year database for {start_year}-{end_year}...")
    
    years_fetched = 0
    years_skipped = 0
    
    for year in range(start_year, end_year + 1):
        # Check if we already have complete data for this year
        if has_complete_year_data(conn, city_name, year):
            print(f"✅ Complete data for {city_name} ({year}) already exists in database.")
            years_skipped += 1
            continue
            
        print(f"🌤️  Fetching complete {year} data from API...")
        
        # Always fetch complete year (Jan 1 - Dec 31)
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)
        
        try:
            data = fetch_weather_data(
                lat, lon,
                year_start.strftime("%Y-%m-%d"),
                year_end.strftime("%Y-%m-%d"),
                config.PARAMETERS
            )

            # Process directly to database (no intermediate CSV)
            process_to_database(data, city_name, country, year)
            years_fetched += 1

        except Exception as e:
            print(f"❌ Error fetching complete data for {year}: {e}")

    # Create ONLY ONE CSV for the requested date range
    print(f"\n🎯 Creating optimized CSV export ({start_date} to {end_date})...")
    output_filename = f"weather_data_{start_date}_to_{end_date}.csv"
    output_path = os.path.join(folder, output_filename)
    
    record_count = export_requested_data_to_csv(conn, city_name, start_date, end_date, output_path)
    
    conn.close()
    
    print(f"\n✅ Process complete!")
    print(f"📊 Database updated: {years_fetched} years fetched, {years_skipped} years already existed")
    print(f"📁 Single CSV created: {output_path} ({record_count} records)")
    print(f"💾 No redundant files - all complete data stored efficiently in database")

if __name__ == "__main__":
    main()
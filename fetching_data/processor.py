# processor.py
import pandas as pd
import os
from database import insert_dataframe_to_db

def process_to_database(data, city_name, country, year):
    """Process API data directly to database without intermediate CSV."""
    if "daily" not in data:
        print("⚠️ No 'daily' data found in API response.")
        return

    df = pd.DataFrame(data["daily"])

    cols = [
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "rain_sum",
        "snowfall_sum",
        "sunshine_duration"
    ]
    df = df[[c for c in cols if c in df.columns]]

    # Insert directly into database
    insert_dataframe_to_db(df, city_name, country, year)
    print(f"✅ Stored complete {year} data in database")
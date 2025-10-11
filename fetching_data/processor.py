# processor.py
import pandas as pd
import os

def process_and_save(data, folder, filename):
    """Convert JSON weather data to CSV and save in the specified folder."""
    if "daily" not in data:
        print("⚠️ No 'daily' data found in API response.")
        return

    os.makedirs(folder, exist_ok=True)
    daily_data = data["daily"]
    df = pd.DataFrame(daily_data)

    # Order columns (if they exist)
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

    path = os.path.join(folder, filename)
    df.to_csv(path, index=False)
    print(f"✅ Saved: {path}")

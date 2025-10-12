# database.py
import mysql.connector
from mysql.connector import errorcode
import config
import pandas as pd

def create_connection():
    """Connect to MySQL server and ensure database exists."""
    try:
        # First connect without database to create it if needed
        conn = mysql.connector.connect(
            host=config.MYSQL_CONFIG["host"],
            user=config.MYSQL_CONFIG["user"],
            password=config.MYSQL_CONFIG["password"],
            port=config.MYSQL_CONFIG["port"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_CONFIG['database']}")
        conn.database = config.MYSQL_CONFIG["database"]
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Database access denied. Check username/password in .env file.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("❌ Database does not exist.")
        else:
            print(f"❌ Database error: {err}")
        raise

def create_main_table(conn):
    """Create the unified weather_data table if not exists."""
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS weather_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city VARCHAR(255),
        country VARCHAR(255),
        date DATE,
        temperature_max FLOAT,
        temperature_min FLOAT,
        apparent_temp_max FLOAT,
        apparent_temp_min FLOAT,
        rain_sum FLOAT,
        snowfall_sum FLOAT,
        sunshine_duration FLOAT,
        year INT,
        UNIQUE KEY uniq_city_date (city, date),
        INDEX idx_city_year_date (city, year, date)
    );
    """
    cursor.execute(query)
    conn.commit()

def has_complete_year_data(conn, city_name, year):
    """Check if we have complete data for a given year (365/366 days)."""
    cursor = conn.cursor()
    
    # Determine expected days for the year
    is_leap_year = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
    expected_days = 366 if is_leap_year else 365
    
    query = """
    SELECT COUNT(DISTINCT date) as unique_days
    FROM weather_data 
    WHERE city = %s AND year = %s
    """
    cursor.execute(query, (city_name, year))
    actual_days = cursor.fetchone()[0]
    
    return actual_days == expected_days

def insert_dataframe_to_db(df, city_name, country, year):
    """Insert pandas DataFrame into MySQL (skip duplicates automatically)."""
    conn = create_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT IGNORE INTO weather_data (
        city, country, date, temperature_max, temperature_min,
        apparent_temp_max, apparent_temp_min, rain_sum,
        snowfall_sum, sunshine_duration, year
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    inserted_count = 0
    for _, row in df.iterrows():
        cursor.execute(insert_query, (
            city_name, country, row["time"],
            row.get("temperature_2m_max"),
            row.get("temperature_2m_min"),
            row.get("apparent_temperature_max"),
            row.get("apparent_temperature_min"),
            row.get("rain_sum"),
            row.get("snowfall_sum"),
            row.get("sunshine_duration"),
            year
        ))
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    conn.close()
    
    if inserted_count > 0:
        print(f"✅ Inserted {inserted_count} new records for {city_name} ({year})")
    else:
        print(f"⚠️ No new records for {city_name} ({year}) - already exists")

def export_requested_data_to_csv(conn, city_name, start_date, end_date, output_path):
    """Export the originally requested date range to CSV from database."""
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT * FROM weather_data 
    WHERE city = %s AND date BETWEEN %s AND %s
    ORDER BY date
    """
    cursor.execute(query, (city_name, start_date, end_date))
    results = cursor.fetchall()
    
    if results:
        df = pd.DataFrame(results)
        # Drop the ID column for cleaner CSV
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        df.to_csv(output_path, index=False)
        print(f"📊 Created CSV: {output_path} ({len(results)} records)")
    else:
        print(f"⚠️ No data found for {city_name} between {start_date} and {end_date}")
    
    return len(results)
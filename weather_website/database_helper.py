# database_helper.py - Fixed database schema
import mysql.connector
from datetime import datetime, timedelta
import requests
import time
import sys
import os

# Direct database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "weather_user", 
    "password": "weather_pass",
    "database": "weather_db",
    "port": 3306
}

def create_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def initialize_database():
    """Initialize database with correct schema"""
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Drop table if exists (for clean start during development)
        # cursor.execute("DROP TABLE IF EXISTS weather_data")
        
        # Create table with correct schema
        create_table_query = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city VARCHAR(255) NOT NULL,
            country VARCHAR(255),
            date DATE NOT NULL,
            temperature_max FLOAT,
            temperature_min FLOAT,
            rain_sum FLOAT,
            sunshine_duration FLOAT,
            year INT,
            latitude FLOAT,
            longitude FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            -- Strong unique constraint to prevent duplicates
            UNIQUE KEY uniq_city_date (city, date),
            -- Index for faster queries
            INDEX idx_city_year_date (city, year, date),
            INDEX idx_city_date (city, date),
            INDEX idx_date (date)
        ) ENGINE=InnoDB;
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ Database table created/verified with correct schema")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_available_cities():
    """Get list of all available cities with duplicate prevention"""
    conn = create_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Use DISTINCT to prevent duplicate cities
        query = "SELECT DISTINCT city, country FROM weather_data ORDER BY city"
        cursor.execute(query)
        cities = cursor.fetchall()
        print(f"✅ Found {len(cities)} unique cities")
        return cities
    except Exception as e:
        print(f"❌ Error fetching cities: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_city_data(city_name, start_date=None, end_date=None):
    """Get weather data for a specific city within date range with duplicate prevention"""
    conn = create_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if start_date and end_date:
            # Use DISTINCT to ensure no duplicate dates
            query = """
                SELECT DISTINCT date, temperature_max, temperature_min, rain_sum, sunshine_duration 
                FROM weather_data 
                WHERE city = %s AND date BETWEEN %s AND %s 
                ORDER BY date
            """
            cursor.execute(query, (city_name, start_date, end_date))
        else:
            query = """
                SELECT DISTINCT date, temperature_max, temperature_min, rain_sum, sunshine_duration 
                FROM weather_data WHERE city = %s ORDER BY date
            """
            cursor.execute(query, (city_name,))
        
        data = cursor.fetchall()
        print(f"✅ Found {len(data)} unique records for {city_name} from {start_date} to {end_date}")
        return data
    except Exception as e:
        print(f"❌ Error fetching weather data for {city_name}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_year_range_from_date_range(start_date, end_date):
    """Convert date range to list of years to ensure complete year coverage"""
    start_year = int(start_date.split('-')[0])
    end_year = int(end_date.split('-')[0])
    
    years = list(range(start_year, end_year + 1))
    print(f"📅 Year range for {start_date} to {end_date}: {years}")
    return years

def check_year_completeness(city_name, year):
    """Check if we have complete data for a specific year"""
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Count unique records for the entire year
        query = """
            SELECT COUNT(DISTINCT date) FROM weather_data 
            WHERE city = %s AND YEAR(date) = %s
        """
        cursor.execute(query, (city_name, year))
        count = cursor.fetchone()[0]
        
        # A complete year should have at least 360 days (accounting for possible missing data)
        is_complete = count >= 360
        print(f"📊 Year {year} completeness: {count}/365 unique days - {'✅ Complete' if is_complete else '❌ Incomplete'}")
        
        return is_complete
        
    except Exception as e:
        print(f"❌ Error checking year completeness: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_date_range_coverage(city_name, start_date, end_date):
    """Check if we have data for the exact date range requested"""
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Count unique records for the exact date range
        query = """
            SELECT COUNT(DISTINCT date) FROM weather_data 
            WHERE city = %s AND date BETWEEN %s AND %s
        """
        cursor.execute(query, (city_name, start_date, end_date))
        count = cursor.fetchone()[0]
        
        # Calculate expected number of days
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        expected_days = (end_dt - start_dt).days + 1
        
        coverage_ratio = count / expected_days if expected_days > 0 else 0
        is_adequate = coverage_ratio >= 0.8  # At least 80% coverage
        
        print(f"📊 Date range coverage: {count}/{expected_days} unique days ({coverage_ratio:.1%}) - {'✅ Adequate' if is_adequate else '❌ Inadequate'}")
        
        return is_adequate
        
    except Exception as e:
        print(f"❌ Error checking date range coverage: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_city_coordinates(city_name):
    """Get coordinates for a city using Open-Meteo Geocoding API with enhanced search"""
    try:
        # Clean the city name
        clean_city = city_name.strip().title()
        
        print(f"🔍 Searching coordinates for: '{clean_city}'")
        
        # Try different search approaches
        search_attempts = [
            clean_city,
            f"{clean_city},",
            clean_city.replace(' ', '%20'),
            clean_city.replace(' ', '+')
        ]
        
        for i, attempt in enumerate(search_attempts):
            print(f"  Attempt {i+1}: {attempt}")
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={attempt}&count=5&language=en"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                print(f"✅ Found coordinates: {result['name']}, {result.get('country', 'Unknown')} "
                      f"({result['latitude']}, {result['longitude']})")
                return {
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'country': result.get('country', 'Unknown'),
                    'name': result['name']
                }
        
        print(f"❌ No coordinates found for any variation of '{city_name}'")
        return None
        
    except Exception as e:
        print(f"❌ Error fetching coordinates for {city_name}: {e}")
        return None

def fetch_weather_data(city_name, start_date, end_date):
    """Fetch weather data from Open-Meteo API for exact date range with duplicate prevention"""
    try:
        # First get coordinates
        coordinates = get_city_coordinates(city_name)
        if not coordinates:
            print(f"❌ Could not find coordinates for {city_name}")
            return None
        
        print(f"📍 Fetching data for {city_name} from {start_date} to {end_date}: "
              f"{coordinates['latitude']}, {coordinates['longitude']}")
        
        # Open-Meteo API call for exact date range
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': coordinates['latitude'],
            'longitude': coordinates['longitude'],
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,temperature_2m_min,rain_sum,sunshine_duration',
            'timezone': 'auto'
        }
        
        print(f"🌐 API Request: {url}")
        print(f"📋 Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'daily' not in data:
            print(f"❌ No weather data found for {city_name} from {start_date} to {end_date}")
            if 'error' in data:
                print(f"🔧 API Error: {data['error']}")
            if 'reason' in data:
                print(f"🔧 API Reason: {data['reason']}")
            return None
        
        # Process the data with duplicate prevention
        daily_data = data['daily']
        processed_data = []
        seen_dates = set()
        
        for i in range(len(daily_data['time'])):
            date_str = daily_data['time'][i]
            
            # Skip if we've already seen this date (shouldn't happen with API, but just in case)
            if date_str in seen_dates:
                print(f"⚠️ Skipping duplicate date from API: {date_str}")
                continue
                
            seen_dates.add(date_str)
            
            processed_data.append({
                'date': date_str,
                'temperature_max': daily_data['temperature_2m_max'][i],
                'temperature_min': daily_data['temperature_2m_min'][i],
                'rain_sum': daily_data['rain_sum'][i],
                'sunshine_duration': daily_data['sunshine_duration'][i],
                'city': coordinates['name'],
                'country': coordinates['country'],
                'latitude': coordinates['latitude'],
                'longitude': coordinates['longitude']
            })
        
        print(f"✅ Fetched {len(processed_data)} unique days of weather data from {start_date} to {end_date}")
        return processed_data
        
    except Exception as e:
        print(f"❌ Error fetching from Open-Meteo for {city_name} from {start_date} to {end_date}: {e}")
        return None

def fetch_weather_data_for_year(city_name, year):
    """Fetch complete year data from Open-Meteo API with duplicate prevention"""
    try:
        # First get coordinates
        coordinates = get_city_coordinates(city_name)
        if not coordinates:
            return None
        
        print(f"📍 Fetching year {year} for {city_name}: {coordinates['latitude']}, {coordinates['longitude']}")
        
        # Set date range for entire year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Open-Meteo API call
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': coordinates['latitude'],
            'longitude': coordinates['longitude'],
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,temperature_2m_min,rain_sum,sunshine_duration',
            'timezone': 'auto'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'daily' not in data:
            print(f"❌ No weather data found for {city_name} in {year}")
            return None
        
        # Process the data with duplicate prevention
        daily_data = data['daily']
        processed_data = []
        seen_dates = set()
        
        for i in range(len(daily_data['time'])):
            date_str = daily_data['time'][i]
            
            # Skip if we've already seen this date
            if date_str in seen_dates:
                print(f"⚠️ Skipping duplicate date from API: {date_str}")
                continue
                
            seen_dates.add(date_str)
            
            processed_data.append({
                'date': date_str,
                'temperature_max': daily_data['temperature_2m_max'][i],
                'temperature_min': daily_data['temperature_2m_min'][i],
                'rain_sum': daily_data['rain_sum'][i],
                'sunshine_duration': daily_data['sunshine_duration'][i],
                'city': coordinates['name'],
                'country': coordinates['country'],
                'latitude': coordinates['latitude'],
                'longitude': coordinates['longitude']
            })
        
        print(f"✅ Fetched {len(processed_data)} unique days of weather data for {year}")
        return processed_data
        
    except Exception as e:
        print(f"❌ Error fetching from Open-Meteo for {city_name} in {year}: {e}")
        return None

def store_weather_data(weather_data):
    """Store weather data in database with enhanced duplicate prevention"""
    if not weather_data:
        return False
    
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # First, let's check if the table has the updated_at column
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'weather_data' 
            AND TABLE_SCHEMA = DATABASE()
            AND COLUMN_NAME = 'updated_at'
        """)
        has_updated_at = cursor.fetchone() is not None
        
        # Build the insert query based on available columns
        if has_updated_at:
            insert_query = """
            INSERT INTO weather_data 
            (city, country, date, temperature_max, temperature_min, rain_sum, sunshine_duration, year, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                temperature_max = VALUES(temperature_max),
                temperature_min = VALUES(temperature_min),
                rain_sum = VALUES(rain_sum),
                sunshine_duration = VALUES(sunshine_duration),
                updated_at = CURRENT_TIMESTAMP
            """
        else:
            # Fallback without updated_at column
            insert_query = """
            INSERT INTO weather_data 
            (city, country, date, temperature_max, temperature_min, rain_sum, sunshine_duration, year, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                temperature_max = VALUES(temperature_max),
                temperature_min = VALUES(temperature_min),
                rain_sum = VALUES(rain_sum),
                sunshine_duration = VALUES(sunshine_duration)
            """
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        for record in weather_data:
            # Extract year from date for database organization
            year = int(record['date'].split('-')[0])
            
            try:
                cursor.execute(insert_query, (
                    record['city'],
                    record['country'],
                    record['date'],
                    record['temperature_max'],
                    record['temperature_min'],
                    record['rain_sum'],
                    record['sunshine_duration'],
                    year,
                    record['latitude'],
                    record['longitude']
                ))
                
                if cursor.rowcount == 1:
                    inserted_count += 1
                elif cursor.rowcount == 2:  # ON DUPLICATE KEY UPDATE returns 2 for updates
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except mysql.connector.Error as e:
                if e.errno == 1062:  # Duplicate entry error
                    skipped_count += 1
                    print(f"⚠️ Skipping duplicate entry for {record['city']} on {record['date']}")
                else:
                    print(f"❌ Database error: {e}")
                    raise e
        
        conn.commit()
        print(f"✅ Database operation: {inserted_count} inserted, {updated_count} updated, {skipped_count} skipped for {weather_data[0]['city']}")
        return inserted_count > 0 or updated_count > 0
        
    except Exception as e:
        print(f"❌ Error storing weather data: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def ensure_year_data(city_name, year):
    """Ensure we have complete data for a specific year"""
    # Check if year is complete
    if check_year_completeness(city_name, year):
        print(f"✅ Year {year} already complete for {city_name}")
        return True
    
    print(f"📥 Year {year} incomplete for {city_name}, fetching complete year...")
    
    # Fetch complete year data
    weather_data = fetch_weather_data_for_year(city_name, year)
    
    if not weather_data:
        print(f"❌ Failed to fetch data for {city_name} in {year}")
        return False
    
    # Store the data
    success = store_weather_data(weather_data)
    
    if success:
        print(f"✅ Successfully stored/updated complete year {year} for {city_name}")
        return True
    else:
        print(f"❌ Failed to store data for {city_name} in {year}")
        return False

def ensure_date_range_data(city_name, start_date, end_date):
    """Ensure we have adequate data for the exact date range"""
    # Check if we have adequate coverage for the exact date range
    if check_date_range_coverage(city_name, start_date, end_date):
        print(f"✅ Date range {start_date} to {end_date} already has adequate coverage for {city_name}")
        return True
    
    print(f"📥 Date range {start_date} to {end_date} has inadequate coverage for {city_name}, fetching exact range...")
    
    # Fetch data for the exact date range
    weather_data = fetch_weather_data(city_name, start_date, end_date)
    
    if not weather_data:
        print(f"❌ Failed to fetch data for {city_name} from {start_date} to {end_date}")
        return False
    
    # Store the data
    success = store_weather_data(weather_data)
    
    if success:
        print(f"✅ Successfully stored/updated data for {city_name} from {start_date} to {end_date}")
        return True
    else:
        print(f"❌ Failed to store data for {city_name} from {start_date} to {end_date}")
        return False

def get_or_fetch_city_data(city_name, start_date, end_date):
    """Get data from database, ensuring both complete years AND exact date range coverage with duplicate prevention"""
    print(f"🔍 Requested: '{city_name}' from {start_date} to {end_date}")
    
    # First, ensure we have adequate data for the exact date range
    if not ensure_date_range_data(city_name, start_date, end_date):
        print(f"⚠️ Could not ensure adequate data for exact date range, but will try with available data")
    
    # Additionally, ensure we have complete data for all years in the range
    # This helps with future queries for the same years
    years = get_year_range_from_date_range(start_date, end_date)
    
    for year in years:
        if not ensure_year_data(city_name, year):
            print(f"⚠️ Could not ensure complete data for {year}, but will try with available data")
    
    # Now get the data for the exact requested date range
    data = get_city_data(city_name, start_date, end_date)
    
    if data:
        print(f"✅ Returning {len(data)} unique records for exact date range")
        return data
    else:
        print(f"❌ No data available even after fetching attempts")
        return []

# Test function to verify database connection and duplicate prevention
def test_connection():
    """Test database connection and basic queries with duplicate checks"""
    print("🧪 Testing database connection and duplicate prevention...")
    
    # Initialize database first
    if not initialize_database():
        print("❌ Failed to initialize database")
        return False
    
    # Test connection
    conn = create_connection()
    if conn:
        print("✅ Database connection successful")
        
        # Check for existing duplicates
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city, date, COUNT(*) as cnt 
                FROM weather_data 
                GROUP BY city, date 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"⚠️ Found {len(duplicates)} duplicate groups in database")
                for dup in duplicates[:5]:  # Show first 5 duplicates
                    print(f"   - {dup[0]} on {dup[1]}: {dup[2]} records")
            else:
                print("✅ No duplicate records found in database")
        except Exception as e:
            print(f"❌ Error checking for duplicates: {e}")
        
        conn.close()
    else:
        print("❌ Database connection failed")
        return False
    
    # Test cities query
    cities = get_available_cities()
    if cities:
        print(f"✅ Cities query successful: {len(cities)} unique cities found")
        for city in cities[:3]:  # Show first 3 cities
            print(f"   - {city['city']} ({city['country']})")
    else:
        print("❌ No cities found or query failed")
    
    return True

# Function to fix existing database schema
def fix_database_schema():
    """Fix the database schema by adding missing columns"""
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check and add missing columns
        columns_to_add = [
            ('latitude', 'FLOAT'),
            ('longitude', 'FLOAT'),
            ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE weather_data ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except mysql.connector.Error as e:
                if e.errno == 1060:  # Duplicate column name
                    print(f"ℹ️ Column {column_name} already exists")
                else:
                    print(f"❌ Error adding column {column_name}: {e}")
        
        conn.commit()
        print("✅ Database schema updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # First fix the schema, then test
    fix_database_schema()
    test_connection()
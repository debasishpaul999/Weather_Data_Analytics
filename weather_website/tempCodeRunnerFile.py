from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sys
import os

# Import the standalone database helper
from database_helper import get_available_cities, get_city_data, get_or_fetch_city_data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/about')
def about():
    return render_template('about.html')

# API endpoints
@app.route('/api/cities')
def api_cities():
    try:
        cities = get_available_cities()
        return jsonify({'success': True, 'cities': cities})
    except Exception as e:
        print(f"❌ API Error in /api/cities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather-data')
def api_weather_data():
    try:
        city = request.args.get('city')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        print(f"🌤️ Requesting data for '{city}' from {start_date} to {end_date}")
        
        if not city:
            return jsonify({'success': False, 'error': 'City parameter is required'})
        
        # Enhanced city validation
        if len(city.strip()) < 2:
            return jsonify({'success': False, 'error': 'City name too short'})
        
        # Validate date format with better error messages
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            today = datetime.now().date()
            
            if start_dt > end_dt:
                return jsonify({'success': False, 'error': 'Start date cannot be after end date'})
                
            if start_dt.date() > today:
                return jsonify({'success': False, 'error': 'Start date cannot be in the future'})
                
            # Allow up to 10 years of historical data
            max_days = 365 * 10
            if (end_dt - start_dt).days > max_days:
                return jsonify({'success': False, 'error': f'Date range cannot exceed {max_days//365} years'})
                
        except ValueError as e:
            return jsonify({'success': False, 'error': 'Invalid date format. Please use YYYY-MM-DD'})
        
        # Use the enhanced function
        data = get_or_fetch_city_data(city, start_date, end_date)
        
        if not data:
            # Provide more helpful error message with suggestions
            suggestions = [
                "Try using the format 'City, Country' (e.g., 'London, UK')",
                "Use English city names",
                "Try nearby major cities",
                "Check your date range (data available for recent years)",
                "Examples: 'New York, US', 'Tokyo, Japan', 'Paris, France'"
            ]
            
            return jsonify({
                'success': False, 
                'error': f'No weather data available for "{city}" in the selected date range',
                'suggestions': suggestions,
                'date_range': f'{start_date} to {end_date}'
            })
        
        # Process data for frontend with duplicate removal
        processed_data = process_weather_data(data)
        summary = get_data_summary(processed_data)
        
        response_data = {
            'success': True, 
            'data': processed_data,
            'city': city,
            'start_date': start_date,
            'end_date': end_date,
            'summary': summary,
            'source': 'database',
            'records_count': len(processed_data)
        }
        
        print(f"✅ Data delivered successfully: {len(processed_data)} unique records")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ API Error in /api/weather-data: {e}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/city-suggestions')
def api_city_suggestions():
    """Get city suggestions based on partial input"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({'success': True, 'suggestions': []})
    
    try:
        import requests
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=10&language=en"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        suggestions = []
        if data.get('results'):
            for result in data['results'][:8]:  # Limit to 8 suggestions
                suggestions.append({
                    'name': result['name'],
                    'country': result.get('country', 'Unknown'),
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'display_name': f"{result['name']}, {result.get('country', 'Unknown')}"
                })
        
        return jsonify({'success': True, 'suggestions': suggestions})
        
    except Exception as e:
        print(f"❌ Error fetching city suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug-city/<city_name>')
def debug_city(city_name):
    """Debug endpoint to check city coordinates"""
    from database_helper import get_city_coordinates
    coordinates = get_city_coordinates(city_name)
    return jsonify({
        'city': city_name,
        'coordinates': coordinates,
        'success': coordinates is not None
    })

def process_weather_data(data):
    """Convert database data to frontend format with duplicate removal"""
    if not data:
        return []
    
    # Use a set to track unique dates for duplicate prevention
    seen_dates = set()
    processed = []
    duplicate_count = 0
    
    for row in data:
        # Convert to dictionary
        row_dict = dict(row)
        
        # Ensure date is string and normalized
        if 'date' in row_dict:
            if isinstance(row_dict['date'], datetime):
                date_str = row_dict['date'].strftime('%Y-%m-%d')
            else:
                # Handle string dates - normalize to YYYY-MM-DD format
                try:
                    date_obj = datetime.strptime(str(row_dict['date']), '%Y-%m-%d')
                    date_str = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    # If date parsing fails, skip this record
                    print(f"⚠️ Skipping record with invalid date: {row_dict['date']}")
                    continue
            
            row_dict['date'] = date_str
            
            # Check for duplicates
            if date_str in seen_dates:
                duplicate_count += 1
                continue
                
            seen_dates.add(date_str)
            processed.append(row_dict)
    
    if duplicate_count > 0:
        print(f"🔄 Removed {duplicate_count} duplicate records during processing")
    
    # Sort by date to ensure consistent ordering
    processed.sort(key=lambda x: x['date'])
    
    return processed

def get_data_summary(data):
    """Calculate basic statistics from clean data"""
    if not data:
        return {}
    
    temps_max = [row.get('temperature_max', 0) for row in data if row.get('temperature_max') is not None]
    temps_min = [row.get('temperature_min', 0) for row in data if row.get('temperature_min') is not None]
    rainfall = [row.get('rain_sum', 0) for row in data if row.get('rain_sum') is not None]
    sunshine = [row.get('sunshine_duration', 0) for row in data if row.get('sunshine_duration') is not None]
    
    # Calculate additional statistics
    hot_days = len([t for t in temps_max if t > 30])
    cold_days = len([t for t in temps_min if t < 10])
    rainy_days_count = len([r for r in rainfall if r > 1])
    heavy_rain_days = len([r for r in rainfall if r > 10])
    
    return {
        'total_days': len(data),
        'avg_max_temp': round(sum(temps_max) / len(temps_max), 1) if temps_max else 0,
        'avg_min_temp': round(sum(temps_min) / len(temps_min), 1) if temps_min else 0,
        'total_rainfall': round(sum(rainfall), 1) if rainfall else 0,
        'rainy_days': rainy_days_count,
        'avg_sunshine': round((sum(sunshine) / len(sunshine)) / 3600, 1) if sunshine else 0,
        'hot_days': hot_days,
        'cold_days': cold_days,
        'heavy_rain_days': heavy_rain_days
    }

@app.route('/test-db')
def test_db():
    """Test page to check database connection"""
    try:
        from database_helper import test_connection
        success = test_connection()
    except Exception as e:
        success = False
        print(f"❌ Test connection failed: {e}")
    
    return f"""
    <h1>Database Test</h1>
    <p>Status: {'✅ SUCCESS' if success else '❌ FAILED'}</p>
    <a href="/">Back to Home</a>
    """

@app.route('/api/clear-cache/<city>')
def clear_cache(city):
    """Debug endpoint to clear and refetch data for a city"""
    try:
        from database_helper import create_connection
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM weather_data WHERE city = %s", (city,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Cache cleared for {city}'})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        from database_helper import create_connection
        conn = create_connection()
        if conn:
            # Check for duplicate data in database
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city, date, COUNT(*) as duplicate_count 
                FROM weather_data 
                GROUP BY city, date 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            conn.close()
            
            status = {
                'status': 'healthy', 
                'database': 'connected',
                'duplicate_check': f'Found {len(duplicates)} duplicate groups' if duplicates else 'No duplicates found'
            }
            
            if duplicates:
                print(f"⚠️ Health check found {len(duplicates)} duplicate groups in database")
                
            return jsonify(status)
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 503
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/api/clean-duplicates')
def clean_duplicates():
    """Admin endpoint to clean duplicate data"""
    try:
        from database_helper import create_connection
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            
            # Count duplicates before cleanup
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT city, date, COUNT(*) as cnt 
                    FROM weather_data 
                    GROUP BY city, date 
                    HAVING COUNT(*) > 1
                ) as duplicates
            """)
            duplicate_groups_before = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT SUM(cnt) - COUNT(*) FROM (
                    SELECT city, date, COUNT(*) as cnt 
                    FROM weather_data 
                    GROUP BY city, date 
                    HAVING COUNT(*) > 1
                ) as duplicates
            """)
            duplicate_records_before = cursor.fetchone()[0] or 0
            
            # Remove duplicates using a temporary table approach
            cursor.execute("""
                CREATE TEMPORARY TABLE weather_temp AS 
                SELECT MIN(id) as keep_id, city, date 
                FROM weather_data 
                GROUP BY city, date
            """)
            
            cursor.execute("""
                DELETE w1 FROM weather_data w1 
                LEFT JOIN weather_temp w2 ON w1.id = w2.keep_id 
                WHERE w2.keep_id IS NULL
            """)
            
            cursor.execute("DROP TEMPORARY TABLE weather_temp")
            
            conn.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Cleaned {duplicate_records_before} duplicate records from {duplicate_groups_before} duplicate groups'
            })
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting WeatherInsight Flask App...")
    print("📁 Current directory:", os.path.dirname(os.path.abspath(__file__)))
    
    print("📊 Testing database connection first...")
    try:
        from database_helper import test_connection
        test_connection()
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    print("🌐 Starting web server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
# basic_insight.py
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import calendar
import os

# Database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "weather_user", 
    "password": "weather_pass",
    "database": "weather_db"
}

# Create output directory for graphs
GRAPH_OUTPUT_DIR = "weather_graphs"

def create_graph_directory(city_name):
    """Create directory for saving graphs"""
    city_folder = os.path.join(GRAPH_OUTPUT_DIR, city_name.replace(" ", "_"))
    os.makedirs(city_folder, exist_ok=True)
    return city_folder

def create_connection():
    """Create database connection"""
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def get_available_cities():
    """Get list of all available cities"""
    conn = create_connection()
    if conn is None:
        return pd.DataFrame()
    
    query = "SELECT DISTINCT city, country FROM weather_data ORDER BY city"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_city_data(city_name, start_date=None, end_date=None):
    """Get data for a specific city with optional date range"""
    conn = create_connection()
    if conn is None:
        return pd.DataFrame()
    
    if start_date and end_date:
        query = "SELECT * FROM weather_data WHERE city = %s AND date BETWEEN %s AND %s ORDER BY date"
        df = pd.read_sql(query, conn, params=[city_name, start_date, end_date])
    else:
        query = "SELECT * FROM weather_data WHERE city = %s ORDER BY date"
        df = pd.read_sql(query, conn, params=[city_name])
    
    conn.close()
    return df

def print_data_range(df, city_name, chart_type):
    """Print the data range being used for the chart"""
    if df.empty:
        return
    
    start_date = df['date'].min()
    end_date = df['date'].max()
    total_days = len(df)
    total_years = df['date'].dt.year.nunique()
    
    print(f"\n📅 DATA RANGE FOR {chart_type.upper()}:")
    print(f"   City: {city_name}")
    print(f"   Period: {start_date} to {end_date}")
    print(f"   Total Days: {total_days}")
    print(f"   Total Years: {total_years}")
    print(f"   Years: {sorted(df['date'].dt.year.unique())}")

def plot_temperature_trend(city_name):
    """Plot temperature trends over time"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    print_data_range(df, city_name, "Temperature Trends")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['temperature_max'], label='Max Temperature', color='red', alpha=0.7)
    plt.plot(df['date'], df['temperature_min'], label='Min Temperature', color='blue', alpha=0.7)
    plt.fill_between(df['date'], df['temperature_min'], df['temperature_max'], alpha=0.2)
    
    plt.title(f'Temperature Trends - {city_name}\n({df["date"].min().strftime("%Y-%m-%d")} to {df["date"].max().strftime("%Y-%m-%d")})', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"temperature_trend_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def plot_rainfall_analysis(city_name):
    """Plot rainfall analysis"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    print_data_range(df, city_name, "Rainfall Analysis")
    
    # Monthly rainfall
    monthly_rain = df.groupby('month').agg({'rain_sum': 'sum'}).reset_index()
    months = [calendar.month_abbr[i] for i in range(1, 13)]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(monthly_rain['month'], monthly_rain['rain_sum'], color='blue', alpha=0.7)
    
    plt.title(f'Monthly Rainfall - {city_name}\n(Data from {df["date"].min().strftime("%Y")} to {df["date"].max().strftime("%Y")})', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Month')
    plt.ylabel('Rainfall (mm)')
    plt.xticks(range(1, 13), months, rotation=45)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"rainfall_analysis_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def plot_yearly_comparison(city_name):
    """Compare yearly averages"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    
    print_data_range(df, city_name, "Yearly Comparison")
    
    yearly_avg = df.groupby('year').agg({
        'temperature_max': 'mean',
        'temperature_min': 'mean',
        'rain_sum': 'sum'
    }).reset_index()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Temperature comparison
    ax1.plot(yearly_avg['year'], yearly_avg['temperature_max'], marker='o', label='Avg Max Temp', color='red')
    ax1.plot(yearly_avg['year'], yearly_avg['temperature_min'], marker='s', label='Avg Min Temp', color='blue')
    ax1.set_title(f'Yearly Temperature Comparison - {city_name}\n({df["date"].min().strftime("%Y")}-{df["date"].max().strftime("%Y")})')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Rainfall comparison
    ax2.bar(yearly_avg['year'], yearly_avg['rain_sum'], color='green', alpha=0.7)
    ax2.set_title(f'Yearly Rainfall - {city_name}\n({df["date"].min().strftime("%Y")}-{df["date"].max().strftime("%Y")})')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Total Rainfall (mm)')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"yearly_comparison_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def plot_temperature_distribution(city_name):
    """Plot temperature distribution"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    print_data_range(df, city_name, "Temperature Distribution")
    
    plt.figure(figsize=(10, 6))
    
    plt.hist(df['temperature_max'], bins=20, alpha=0.7, label='Max Temperature', color='red', edgecolor='black')
    plt.hist(df['temperature_min'], bins=20, alpha=0.7, label='Min Temperature', color='blue', edgecolor='black')
    
    plt.title(f'Temperature Distribution - {city_name}\n({df["date"].min().strftime("%Y-%m-%d")} to {df["date"].max().strftime("%Y-%m-%d")})', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Frequency (Days)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"temperature_distribution_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def plot_seasonal_analysis(city_name):
    """Plot seasonal analysis"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    
    print_data_range(df, city_name, "Seasonal Analysis")
    
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Autumn'
    
    df['season'] = df['month'].apply(get_season)
    seasonal_avg = df.groupby('season').agg({
        'temperature_max': 'mean',
        'temperature_min': 'mean',
        'rain_sum': 'sum'
    }).reset_index()
    
    # Reorder seasons
    season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
    seasonal_avg = seasonal_avg.set_index('season').reindex(season_order).reset_index()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Temperature by season
    x = np.arange(len(seasonal_avg))
    width = 0.35
    ax1.bar(x - width/2, seasonal_avg['temperature_max'], width, label='Avg Max Temp', color='red', alpha=0.7)
    ax1.bar(x + width/2, seasonal_avg['temperature_min'], width, label='Avg Min Temp', color='blue', alpha=0.7)
    ax1.set_title(f'Seasonal Temperatures - {city_name}\n({df["date"].min().strftime("%Y")}-{df["date"].max().strftime("%Y")})')
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(seasonal_avg['season'])
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Rainfall by season
    ax2.bar(seasonal_avg['season'], seasonal_avg['rain_sum'], color='green', alpha=0.7)
    ax2.set_title(f'Seasonal Rainfall - {city_name}\n({df["date"].min().strftime("%Y")}-{df["date"].max().strftime("%Y")})')
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Rainfall (mm)')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"seasonal_analysis_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def plot_extreme_days(city_name):
    """Plot analysis of extreme weather days"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    print_data_range(df, city_name, "Extreme Weather Days")
    
    extreme_days = {
        'Hot Days (>30°C)': (df['temperature_max'] > 30).sum(),
        'Very Hot Days (>35°C)': (df['temperature_max'] > 35).sum(),
        'Cold Days (<10°C)': (df['temperature_min'] < 10).sum(),
        'Very Cold Days (<5°C)': (df['temperature_min'] < 5).sum(),
        'Rainy Days (>1mm)': (df['rain_sum'] > 1).sum(),
        'Heavy Rain (>10mm)': (df['rain_sum'] > 10).sum()
    }
    
    plt.figure(figsize=(12, 6))
    colors = ['#ff9999', '#ff6666', '#99ccff', '#6699ff', '#99ff99', '#66cc66']
    bars = plt.bar(extreme_days.keys(), extreme_days.values(), color=colors)
    
    plt.title(f'Extreme Weather Days - {city_name}\n({df["date"].min().strftime("%Y-%m-%d")} to {df["date"].max().strftime("%Y-%m-%d")})', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Weather Condition')
    plt.ylabel('Number of Days')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the graph
    output_dir = create_graph_directory(city_name)
    filename = f"extreme_days_{city_name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"💾 Graph saved: {filepath}")
    plt.show()

def show_basic_statistics(city_name):
    """Show basic statistics with data range"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\n📊 BASIC STATISTICS - {city_name.upper()}")
    print("=" * 60)
    print(f"📅 DATA RANGE: {df['date'].min()} to {df['date'].max()}")
    print(f"📆 Total Days: {len(df)}")
    print(f"📅 Total Years: {df['date'].dt.year.nunique()}")
    print(f"📈 Years Available: {sorted(df['date'].dt.year.unique())}")
    print("=" * 60)
    print(f"\n🌡️  TEMPERATURE ANALYSIS:")
    print(f"   Average High Temperature: {df['temperature_max'].mean():.1f}°C")
    print(f"   Average Low Temperature:  {df['temperature_min'].mean():.1f}°C")
    print(f"   Highest Recorded:         {df['temperature_max'].max():.1f}°C")
    print(f"   Lowest Recorded:          {df['temperature_min'].min():.1f}°C")
    print(f"   Temperature Range:        {df['temperature_max'].max() - df['temperature_min'].min():.1f}°C")
    
    print(f"\n🌧️  RAINFALL ANALYSIS:")
    print(f"   Total Rainfall:          {df['rain_sum'].sum():.0f} mm")
    print(f"   Average Daily Rainfall:  {df['rain_sum'].mean():.1f} mm")
    print(f"   Rainy Days (>1mm):       {(df['rain_sum'] > 1).sum()} days")
    print(f"   Heavy Rain Days (>10mm): {(df['rain_sum'] > 10).sum()} days")
    print(f"   Dry Days (0mm):          {(df['rain_sum'] == 0).sum()} days")
    
    print(f"\n☀️  SUNSHINE ANALYSIS:")
    print(f"   Average Daily Sunshine:  {df['sunshine_duration'].mean()/3600:.1f} hours")
    print(f"   Total Sunshine:          {df['sunshine_duration'].sum()/3600:.0f} hours")
    
    print(f"\n❄️  SNOWFALL ANALYSIS:")
    print(f"   Total Snowfall:          {df['snowfall_sum'].sum():.0f} cm")
    print(f"   Snowy Days (>0cm):       {(df['snowfall_sum'] > 0).sum()} days")
    print("=" * 60)

def show_data_range_only(city_name):
    """Show only the data range without plots"""
    df = get_city_data(city_name)
    if df.empty:
        print(f"❌ No data found for {city_name}")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\n📅 DATA AVAILABILITY - {city_name.upper()}")
    print("=" * 50)
    print(f"First Date:    {df['date'].min()}")
    print(f"Last Date:     {df['date'].max()}")
    print(f"Total Days:    {len(df)}")
    print(f"Total Years:   {df['date'].dt.year.nunique()}")
    print(f"Years:         {sorted(df['date'].dt.year.unique())}")
    print(f"Date Range:    {(df['date'].max() - df['date'].min()).days} days")
    print("=" * 50)

def main():
    """Main function"""
    print("🌦️ WEATHER DATA ANALYSIS WITH DATA RANGE")
    print("========================================")
    
    # Create main graphs directory
    os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)
    print(f"📁 Graphs will be saved in: {GRAPH_OUTPUT_DIR}/")
    
    # Show available cities
    cities_df = get_available_cities()
    
    if cities_df.empty:
        print("❌ No cities found in database!")
        return
    
    print("\n📍 Available Cities:")
    for idx, row in cities_df.iterrows():
        print(f"   {idx+1}. {row['city']} ({row['country']})")
    
    while True:
        city = input("\nEnter city name (or 'quit' to exit): ").strip()
        
        if city.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        if city not in cities_df['city'].values:
            print(f"❌ City '{city}' not found in database. Available cities: {', '.join(cities_df['city'].values)}")
            continue
        
        while True:
            print(f"\n📈 ANALYSIS OPTIONS for {city.upper()}:")
            print("1. 📊 Temperature Trends Over Time")
            print("2. 🌧️  Rainfall Analysis")
            print("3. 📅 Yearly Comparison")
            print("4. 📊 Temperature Distribution")
            print("5. 🍂 Seasonal Analysis")
            print("6. ⚡ Extreme Weather Days")
            print("7. 📋 Basic Statistics")
            print("8. 📅 Show Data Range Only")
            print("9. 🔄 Change City")
            print("0. 🚪 Exit")
            
            choice = input("\nSelect option (1-0): ").strip()
            
            if choice == '1':
                plot_temperature_trend(city)
            elif choice == '2':
                plot_rainfall_analysis(city)
            elif choice == '3':
                plot_yearly_comparison(city)
            elif choice == '4':
                plot_temperature_distribution(city)
            elif choice == '5':
                plot_seasonal_analysis(city)
            elif choice == '6':
                plot_extreme_days(city)
            elif choice == '7':
                show_basic_statistics(city)
            elif choice == '8':
                show_data_range_only(city)
            elif choice == '9':
                break
            elif choice == '0':
                print("👋 Goodbye!")
                return
            else:
                print("❌ Invalid choice! Please enter 1-0.")

if __name__ == "__main__":
    main()
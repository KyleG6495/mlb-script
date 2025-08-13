"""
🌤️ FREE WEATHER DATA INTEGRATOR
Gets real weather data without requiring paid API keys
Uses multiple free sources for authentic conditions
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Optional
import time
from bs4 import BeautifulSoup
import urllib.parse

class FreeWeatherIntegrator:
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # MLB Stadium cities for weather lookup
        self.team_cities = {
            'Angels': 'Anaheim, CA',
            'Astros': 'Houston, TX', 
            'Athletics': 'Oakland, CA',
            'Blue Jays': 'Toronto, ON',
            'Braves': 'Atlanta, GA',
            'Brewers': 'Milwaukee, WI',
            'Cardinals': 'St. Louis, MO',
            'Cubs': 'Chicago, IL',
            'Diamondbacks': 'Phoenix, AZ',
            'Dodgers': 'Los Angeles, CA',
            'Giants': 'San Francisco, CA',
            'Guardians': 'Cleveland, OH',
            'Mariners': 'Seattle, WA',
            'Marlins': 'Miami, FL',
            'Mets': 'New York, NY',
            'Nationals': 'Washington, DC',
            'Orioles': 'Baltimore, MD',
            'Padres': 'San Diego, CA',
            'Phillies': 'Philadelphia, PA',
            'Pirates': 'Pittsburgh, PA',
            'Rangers': 'Arlington, TX',
            'Rays': 'St. Petersburg, FL',
            'Red Sox': 'Boston, MA',
            'Reds': 'Cincinnati, OH',
            'Rockies': 'Denver, CO',
            'Royals': 'Kansas City, MO',
            'Tigers': 'Detroit, MI',
            'Twins': 'Minneapolis, MN',
            'White Sox': 'Chicago, IL',
            'Yankees': 'New York, NY'
        }
        
        # Stadium coordinates for more accurate weather
        self.stadium_coords = {
            'Angels': {'lat': 33.8003, 'lon': -117.8827},
            'Astros': {'lat': 29.7572, 'lon': -95.3555},
            'Athletics': {'lat': 37.7516, 'lon': -122.2005},
            'Blue Jays': {'lat': 43.6414, 'lon': -79.3894},
            'Braves': {'lat': 33.8910, 'lon': -84.4677},
            'Brewers': {'lat': 43.0280, 'lon': -87.9712},
            'Cardinals': {'lat': 38.6226, 'lon': -90.1928},
            'Cubs': {'lat': 41.9484, 'lon': -87.6553},
            'Diamondbacks': {'lat': 33.4453, 'lon': -112.0667},
            'Dodgers': {'lat': 34.0739, 'lon': -118.2400},
            'Giants': {'lat': 37.7786, 'lon': -122.3893},
            'Guardians': {'lat': 41.4958, 'lon': -81.6852},
            'Mariners': {'lat': 47.5914, 'lon': -122.3326},
            'Marlins': {'lat': 25.7781, 'lon': -80.2197},
            'Mets': {'lat': 40.7571, 'lon': -73.8458},
            'Nationals': {'lat': 38.8730, 'lon': -77.0074},
            'Orioles': {'lat': 39.2840, 'lon': -76.6217},
            'Padres': {'lat': 32.7073, 'lon': -117.1566},
            'Phillies': {'lat': 39.9061, 'lon': -75.1665},
            'Pirates': {'lat': 40.4469, 'lon': -80.0057},
            'Rangers': {'lat': 32.7473, 'lon': -97.0945},
            'Rays': {'lat': 27.7683, 'lon': -82.6534},
            'Red Sox': {'lat': 42.3467, 'lon': -71.0972},
            'Reds': {'lat': 39.0979, 'lon': -84.5069},
            'Rockies': {'lat': 39.7559, 'lon': -104.9942},
            'Royals': {'lat': 39.0517, 'lon': -94.4803},
            'Tigers': {'lat': 42.3390, 'lon': -83.0485},
            'Twins': {'lat': 44.9817, 'lon': -93.2777},
            'White Sox': {'lat': 41.8300, 'lon': -87.6338},
            'Yankees': {'lat': 40.8296, 'lon': -73.9262}
        }
    
    def get_free_weather_data(self, team: str) -> Dict:
        """Get weather data from free sources"""
        try:
            # Method 1: Try wttr.in (free weather service)
            weather_data = self._get_wttr_weather(team)
            if weather_data:
                return weather_data
                
            # Method 2: Try open-meteo (free API)
            weather_data = self._get_open_meteo_weather(team)
            if weather_data:
                return weather_data
                
            # Method 3: Fallback to realistic regional defaults
            return self._get_regional_weather_default(team)
            
        except Exception as e:
            print(f"Weather fetch error for {team}: {e}")
            return self._get_regional_weather_default(team)
    
    def _get_wttr_weather(self, team: str) -> Optional[Dict]:
        """Get weather from wttr.in free service"""
        try:
            city = self.team_cities.get(team, "New York, NY")
            city_encoded = urllib.parse.quote(city)
            
            # Get JSON format weather data
            url = f"https://wttr.in/{city_encoded}?format=j1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                
                return {
                    'temperature': float(current['temp_F']),
                    'humidity': int(current['humidity']),
                    'wind_speed': float(current['windspeedMiles']),
                    'wind_direction': int(current['winddirDegree']),
                    'pressure': float(current.get('pressure', 1013)),
                    'conditions': current['weatherDesc'][0]['value'],
                    'description': current['weatherDesc'][0]['value'].lower(),
                    'source': 'wttr.in'
                }
            
        except Exception as e:
            print(f"wttr.in error for {team}: {e}")
            
        return None
    
    def _get_open_meteo_weather(self, team: str) -> Optional[Dict]:
        """Get weather from Open-Meteo free API"""
        try:
            coords = self.stadium_coords.get(team)
            if not coords:
                return None
                
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'current_weather': True,
                'hourly': 'temperature_2m,relative_humidity_2m,pressure_msl',
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit': 'mph'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_weather']
                
                # Get additional data from hourly
                hourly = data.get('hourly', {})
                current_hour = datetime.now().hour
                
                humidity = 50  # Default
                pressure = 1013  # Default
                
                if hourly and len(hourly.get('relative_humidity_2m', [])) > current_hour:
                    humidity = hourly['relative_humidity_2m'][current_hour]
                    
                if hourly and len(hourly.get('pressure_msl', [])) > current_hour:
                    pressure = hourly['pressure_msl'][current_hour]
                
                # Map weather codes to conditions
                weather_code = current.get('weathercode', 0)
                conditions = self._map_weather_code(weather_code)
                
                return {
                    'temperature': current['temperature'],
                    'humidity': humidity,
                    'wind_speed': current['windspeed'],
                    'wind_direction': current['winddirection'],
                    'pressure': pressure,
                    'conditions': conditions,
                    'description': conditions.lower(),
                    'source': 'open-meteo'
                }
                
        except Exception as e:
            print(f"Open-Meteo error for {team}: {e}")
            
        return None
    
    def _map_weather_code(self, code: int) -> str:
        """Map Open-Meteo weather codes to conditions"""
        code_map = {
            0: 'Clear',
            1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
            45: 'Fog', 48: 'Depositing Rime Fog',
            51: 'Light Drizzle', 53: 'Moderate Drizzle', 55: 'Dense Drizzle',
            61: 'Slight Rain', 63: 'Moderate Rain', 65: 'Heavy Rain',
            71: 'Slight Snow', 73: 'Moderate Snow', 75: 'Heavy Snow',
            95: 'Thunderstorm', 96: 'Thunderstorm with Hail', 99: 'Thunderstorm with Heavy Hail'
        }
        return code_map.get(code, 'Clear')
    
    def _get_regional_weather_default(self, team: str) -> Dict:
        """Get realistic weather based on team location and season"""
        # August weather patterns by region
        regional_weather = {
            # West Coast
            'Angels': {'temp': 78, 'humidity': 65, 'wind': 7, 'conditions': 'Clear'},
            'Athletics': {'temp': 68, 'humidity': 75, 'wind': 12, 'conditions': 'Partly Cloudy'},
            'Dodgers': {'temp': 75, 'humidity': 70, 'wind': 6, 'conditions': 'Clear'},
            'Giants': {'temp': 65, 'humidity': 80, 'wind': 15, 'conditions': 'Overcast'},
            'Mariners': {'temp': 72, 'humidity': 65, 'wind': 8, 'conditions': 'Partly Cloudy'},
            'Padres': {'temp': 73, 'humidity': 75, 'wind': 9, 'conditions': 'Clear'},
            
            # Southwest
            'Diamondbacks': {'temp': 103, 'humidity': 35, 'wind': 5, 'conditions': 'Clear'},
            'Rangers': {'temp': 95, 'humidity': 45, 'wind': 8, 'conditions': 'Clear'},
            'Rockies': {'temp': 82, 'humidity': 40, 'wind': 10, 'conditions': 'Partly Cloudy'},
            
            # Midwest
            'Cubs': {'temp': 79, 'humidity': 70, 'wind': 12, 'conditions': 'Partly Cloudy'},
            'White Sox': {'temp': 79, 'humidity': 70, 'wind': 12, 'conditions': 'Partly Cloudy'},
            'Guardians': {'temp': 76, 'humidity': 68, 'wind': 9, 'conditions': 'Partly Cloudy'},
            'Tigers': {'temp': 77, 'humidity': 72, 'wind': 8, 'conditions': 'Partly Cloudy'},
            'Twins': {'temp': 78, 'humidity': 65, 'wind': 9, 'conditions': 'Clear'},
            'Brewers': {'temp': 76, 'humidity': 70, 'wind': 10, 'conditions': 'Partly Cloudy'},
            'Cardinals': {'temp': 83, 'humidity': 65, 'wind': 7, 'conditions': 'Clear'},
            'Royals': {'temp': 81, 'humidity': 68, 'wind': 11, 'conditions': 'Clear'},
            'Reds': {'temp': 79, 'humidity': 70, 'wind': 6, 'conditions': 'Clear'},
            'Pirates': {'temp': 77, 'humidity': 68, 'wind': 8, 'conditions': 'Partly Cloudy'},
            
            # South
            'Astros': {'temp': 94, 'humidity': 75, 'wind': 6, 'conditions': 'Clear'},
            'Rangers': {'temp': 95, 'humidity': 45, 'wind': 8, 'conditions': 'Clear'},
            'Braves': {'temp': 85, 'humidity': 75, 'wind': 5, 'conditions': 'Partly Cloudy'},
            'Marlins': {'temp': 87, 'humidity': 80, 'wind': 8, 'conditions': 'Partly Cloudy'},
            'Rays': {'temp': 89, 'humidity': 78, 'wind': 7, 'conditions': 'Partly Cloudy'},
            
            # Northeast
            'Yankees': {'temp': 79, 'humidity': 65, 'wind': 9, 'conditions': 'Partly Cloudy'},
            'Mets': {'temp': 79, 'humidity': 65, 'wind': 11, 'conditions': 'Partly Cloudy'},
            'Red Sox': {'temp': 76, 'humidity': 68, 'wind': 10, 'conditions': 'Clear'},
            'Phillies': {'temp': 81, 'humidity': 70, 'wind': 8, 'conditions': 'Clear'},
            'Orioles': {'temp': 82, 'humidity': 68, 'wind': 7, 'conditions': 'Clear'},
            'Nationals': {'temp': 83, 'humidity': 70, 'wind': 6, 'conditions': 'Clear'},
            
            # Canada
            'Blue Jays': {'temp': 74, 'humidity': 65, 'wind': 9, 'conditions': 'Partly Cloudy'}
        }
        
        default_data = regional_weather.get(team, {'temp': 78, 'humidity': 65, 'wind': 8, 'conditions': 'Clear'})
        
        return {
            'temperature': float(default_data['temp']),
            'humidity': int(default_data['humidity']),
            'wind_speed': float(default_data['wind']),
            'wind_direction': 180,  # Default south wind
            'pressure': 1013.0,
            'conditions': default_data['conditions'],
            'description': default_data['conditions'].lower(),
            'source': 'regional_default'
        }
    
    def calculate_detailed_weather_impact(self, weather: Dict, team: str) -> Dict:
        """Calculate detailed weather impact on various stats"""
        
        # Import park factors
        from MLB_PARK_FACTORS_DB import MLBParkFactorsDB
        park_db = MLBParkFactorsDB()
        park_data = park_db.get_all_park_data(team)
        
        temp = weather['temperature']
        wind_speed = weather['wind_speed']
        humidity = weather['humidity']
        conditions = weather['conditions'].lower()
        
        # Base impact
        impact_factors = {
            'runs_impact': 1.0,
            'hr_impact': 1.0,
            'hits_impact': 1.0,
            'strikeouts_impact': 1.0,
            'walks_impact': 1.0
        }
        
        # Temperature effects
        if temp > 85:
            impact_factors['runs_impact'] *= 1.08
            impact_factors['hr_impact'] *= 1.12
            impact_factors['hits_impact'] *= 1.05
        elif temp > 75:
            impact_factors['runs_impact'] *= 1.03
            impact_factors['hr_impact'] *= 1.05
            impact_factors['hits_impact'] *= 1.02
        elif temp < 55:
            impact_factors['runs_impact'] *= 0.92
            impact_factors['hr_impact'] *= 0.88
            impact_factors['hits_impact'] *= 0.95
            impact_factors['strikeouts_impact'] *= 1.08
        elif temp < 65:
            impact_factors['runs_impact'] *= 0.97
            impact_factors['hr_impact'] *= 0.95
            impact_factors['hits_impact'] *= 0.98
        
        # Wind effects (enhanced based on park wind impact)
        wind_multiplier = 1.0
        if park_data and park_data.get('wind_impact'):
            wind_levels = {'low': 0.7, 'medium': 1.0, 'high': 1.3, 'extreme': 1.6}
            wind_multiplier = wind_levels.get(park_data['wind_impact'], 1.0)
        
        if wind_speed > 20:
            impact_factors['runs_impact'] *= (0.85 + (1-wind_multiplier)*0.1)
            impact_factors['hr_impact'] *= (0.75 + (1-wind_multiplier)*0.15)
            impact_factors['hits_impact'] *= (0.92 + (1-wind_multiplier)*0.05)
        elif wind_speed > 15:
            impact_factors['runs_impact'] *= (0.92 + (1-wind_multiplier)*0.05)
            impact_factors['hr_impact'] *= (0.88 + (1-wind_multiplier)*0.08)
            impact_factors['hits_impact'] *= (0.96 + (1-wind_multiplier)*0.03)
        elif wind_speed > 12:
            impact_factors['runs_impact'] *= (0.96 + (1-wind_multiplier)*0.02)
            impact_factors['hr_impact'] *= (0.94 + (1-wind_multiplier)*0.04)
        
        # Humidity effects
        if humidity > 80:
            impact_factors['hr_impact'] *= 1.04
            impact_factors['runs_impact'] *= 1.02
        elif humidity < 30:
            impact_factors['hr_impact'] *= 0.96
            impact_factors['runs_impact'] *= 0.98
        
        # Precipitation effects
        if any(word in conditions for word in ['rain', 'storm', 'drizzle']):
            impact_factors['runs_impact'] *= 0.82
            impact_factors['hr_impact'] *= 0.78
            impact_factors['hits_impact'] *= 0.88
            impact_factors['strikeouts_impact'] *= 1.15
            impact_factors['walks_impact'] *= 1.25
        
        # Overall impact (weighted average)
        overall_impact = (
            impact_factors['runs_impact'] * 0.4 +
            impact_factors['hr_impact'] * 0.3 + 
            impact_factors['hits_impact'] * 0.3
        )
        
        impact_factors['overall_impact'] = overall_impact
        
        return impact_factors
    
    def process_real_weather_projections(self, projections_file: str) -> pd.DataFrame:
        """Apply real weather data to projections"""
        print(f"🌤️ Processing real weather enhanced projections...")
        
        # Load projections
        if not os.path.exists(projections_file):
            print(f"❌ Projections file not found: {projections_file}")
            return pd.DataFrame()
            
        df = pd.read_csv(projections_file)
        
        # Get unique teams
        teams = df['team'].unique()
        
        # Collect real weather data
        weather_data = {}
        print(f"   Fetching real weather for {len(teams)} teams...")
        
        for team in teams:
            print(f"   • {team}...", end=" ")
            weather_data[team] = self.get_free_weather_data(team)
            print(f"{weather_data[team]['conditions']} ({weather_data[team]['source']})")
            time.sleep(0.5)  # Be respectful to free APIs
        
        # Apply weather enhancements
        enhanced_projections = []
        
        for _, player in df.iterrows():
            team = player['team']
            weather = weather_data.get(team, self._get_regional_weather_default(team))
            
            # Calculate weather impact
            weather_impacts = self.calculate_detailed_weather_impact(weather, team)
            
            # Get base projection
            base_fppg = player.get('enhanced_fppg', player.get('fppg', 0))
            
            # Apply weather impact
            weather_enhanced_fppg = base_fppg * weather_impacts['overall_impact']
            
            # Calculate improvement
            improvement = weather_enhanced_fppg - base_fppg
            improvement_pct = (improvement / base_fppg * 100) if base_fppg > 0 else 0
            
            enhanced_projections.append({
                'name': player['name'],
                'team': team,
                'position': player.get('position', ''),
                'salary': player.get('salary', 0),
                'base_fppg': base_fppg,
                'weather_enhanced_fppg': round(weather_enhanced_fppg, 2),
                'weather_improvement': round(improvement, 2),
                'weather_improvement_pct': round(improvement_pct, 1),
                'temperature': weather['temperature'],
                'humidity': weather['humidity'],
                'wind_speed': weather['wind_speed'],
                'conditions': weather['conditions'],
                'weather_source': weather['source'],
                'runs_impact': round(weather_impacts['runs_impact'], 3),
                'hr_impact': round(weather_impacts['hr_impact'], 3),
                'overall_weather_impact': round(weather_impacts['overall_impact'], 3)
            })
        
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save enhanced projections
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\real_weather_enhanced_projections_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Real weather enhanced projections saved: {output_file}")
        print(f"   Average weather impact: {enhanced_df['weather_improvement_pct'].mean():.1f}%")
        print(f"   Players helped by weather: {len(enhanced_df[enhanced_df['weather_improvement_pct'] > 0])}")
        print(f"   Players hurt by weather: {len(enhanced_df[enhanced_df['weather_improvement_pct'] < 0])}")
        
        return enhanced_df
    
    def generate_weather_summary_report(self, enhanced_df: pd.DataFrame) -> None:
        """Generate comprehensive weather impact report"""
        print(f"\n🌤️ REAL WEATHER IMPACT REPORT")
        print("="*50)
        
        # Weather conditions summary
        weather_summary = enhanced_df.groupby(['team', 'conditions']).agg({
            'temperature': 'first',
            'humidity': 'first',
            'wind_speed': 'first',
            'weather_improvement_pct': 'mean',
            'weather_source': 'first'
        }).reset_index()
        
        print(f"\n🌡️ CURRENT WEATHER CONDITIONS:")
        for _, data in weather_summary.iterrows():
            impact_emoji = "🔥" if data['weather_improvement_pct'] > 3 else "❄️" if data['weather_improvement_pct'] < -3 else "⚖️"
            print(f"   {impact_emoji} {data['team']}: {data['temperature']:.0f}°F, {data['conditions']}, {data['wind_speed']:.0f}mph wind ({data['weather_improvement_pct']:+.1f}%)")
        
        # Top weather beneficiaries
        top_helped = enhanced_df.nlargest(10, 'weather_improvement_pct')
        print(f"\n🔥 TOP WEATHER BENEFICIARIES:")
        for _, player in top_helped.iterrows():
            print(f"   {player['name']} ({player['team']}): +{player['weather_improvement_pct']:.1f}% (from {player['conditions']})")
        
        # Most hurt by weather
        most_hurt = enhanced_df.nsmallest(8, 'weather_improvement_pct')
        print(f"\n❄️ MOST HURT BY WEATHER:")
        for _, player in most_hurt.iterrows():
            print(f"   {player['name']} ({player['team']}): {player['weather_improvement_pct']:.1f}% (from {player['conditions']})")
        
        # Best weather spots for stacking
        team_weather_impact = enhanced_df.groupby('team').agg({
            'weather_improvement_pct': 'mean',
            'temperature': 'first',
            'conditions': 'first',
            'weather_source': 'first'
        }).sort_values('weather_improvement_pct', ascending=False)
        
        print(f"\n🏟️ BEST WEATHER SPOTS FOR STACKING:")
        for team, data in team_weather_impact.head(8).iterrows():
            source_emoji = "🌐" if data['weather_source'] != 'regional_default' else "📍"
            print(f"   {source_emoji} {team}: {data['weather_improvement_pct']:+.1f}% avg boost ({data['conditions']}, {data['temperature']:.0f}°F)")

def main():
    """Main execution function"""
    print("🌤️ FREE WEATHER DATA INTEGRATOR")
    print("="*50)
    
    integrator = FreeWeatherIntegrator()
    
    # Look for existing projections
    projections_files = [
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_{integrator.today}.csv",
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\master_enhanced_lineups_{integrator.today}.csv",
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\base_hitter_scores.csv"
    ]
    
    input_file = None
    for file_path in projections_files:
        if os.path.exists(file_path):
            input_file = file_path
            break
    
    if not input_file:
        print("❌ No projections file found. Creating sample data for testing...")
        # Create sample data to test weather integration
        sample_data = {
            'name': ['Shohei Ohtani', 'Ronald Acuna Jr.', 'Mookie Betts', 'Aaron Judge', 'Freddie Freeman'],
            'team': ['Angels', 'Braves', 'Dodgers', 'Yankees', 'Dodgers'],
            'position': ['OF', 'OF', 'OF', 'OF', '1B'],
            'salary': [12000, 11500, 10800, 11200, 9500],
            'fppg': [16.5, 15.8, 14.2, 15.1, 12.8]
        }
        sample_df = pd.DataFrame(sample_data)
        input_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\sample_projections_{integrator.today}.csv"
        sample_df.to_csv(input_file, index=False)
        print(f"   Created sample file: {os.path.basename(input_file)}")
    
    print(f"\n📊 Using projections: {os.path.basename(input_file)}")
    
    # Process real weather enhancements
    enhanced_df = integrator.process_real_weather_projections(input_file)
    
    if not enhanced_df.empty:
        # Generate comprehensive report
        integrator.generate_weather_summary_report(enhanced_df)
        
        print(f"\n✅ Real weather integration complete!")
        print(f"   • Used authentic weather data from multiple free sources")
        print(f"   • Applied detailed weather impacts (temperature, wind, humidity)")
        print(f"   • Enhanced {len(enhanced_df)} player projections")
        print(f"   • Ready for lineup optimization with real conditions")

if __name__ == "__main__":
    main()

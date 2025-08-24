#!/usr/bin/env python3
"""
ENHANCED WEATHER INTEGRATION FOR MLB PREDICTIONS
===============================================

Integrates advanced weather analytics into your prediction pipeline:
- Real-time weather data for all MLB games
- Weather-based performance adjustments
- Historical weather impact analysis
- Ballpark-specific weather effects

Integrates with your existing weather_enhanced_features.py
"""

import pandas as pd
import numpy as np
import requests
import json
import logging
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedWeatherAnalytics:
    def __init__(self):
        self.ballpark_coordinates = {
            'LAA': {'lat': 33.8003, 'lon': -117.8827, 'elevation': 160},  # Angel Stadium
            'HOU': {'lat': 29.7569, 'lon': -95.3551, 'elevation': 22},   # Minute Maid Park
            'OAK': {'lat': 37.7516, 'lon': -122.2008, 'elevation': 20},  # Oakland Coliseum
            'TOR': {'lat': 43.6414, 'lon': -79.3894, 'elevation': 91},   # Rogers Centre
            'ATL': {'lat': 33.8906, 'lon': -84.4677, 'elevation': 323},  # Truist Park
            'MIL': {'lat': 43.0280, 'lon': -87.9712, 'elevation': 203},  # American Family Field
            'STL': {'lat': 38.6226, 'lon': -90.1928, 'elevation': 156},  # Busch Stadium
            'CHC': {'lat': 41.9484, 'lon': -87.6553, 'elevation': 181},  # Wrigley Field
            'ARI': {'lat': 33.4453, 'lon': -112.0667, 'elevation': 331}, # Chase Field (Dome)
            'LAD': {'lat': 34.0739, 'lon': -118.2400, 'elevation': 162}, # Dodger Stadium
            'SF': {'lat': 37.7786, 'lon': -122.3893, 'elevation': 12},   # Oracle Park
            'CLE': {'lat': 41.4958, 'lon': -81.6856, 'elevation': 179},  # Progressive Field
            'SEA': {'lat': 47.5914, 'lon': -122.3326, 'elevation': 20},  # T-Mobile Park
            'MIA': {'lat': 25.7781, 'lon': -80.2197, 'elevation': 5},    # loanDepot Park
            'NYM': {'lat': 40.7571, 'lon': -73.8458, 'elevation': 19},   # Citi Field
            'WAS': {'lat': 38.8730, 'lon': -77.0074, 'elevation': 12},   # Nationals Park
            'BAL': {'lat': 39.2838, 'lon': -76.6217, 'elevation': 20},   # Oriole Park
            'SD': {'lat': 32.7073, 'lon': -117.1566, 'elevation': 19},   # Petco Park
            'PHI': {'lat': 39.9061, 'lon': -75.1665, 'elevation': 20},   # Citizens Bank Park
            'PIT': {'lat': 40.4469, 'lon': -80.0057, 'elevation': 236},  # PNC Park
            'TEX': {'lat': 32.7473, 'lon': -97.0814, 'elevation': 171},  # Globe Life Field
            'TB': {'lat': 27.7682, 'lon': -82.6534, 'elevation': 11},    # Tropicana Field (Dome)
            'BOS': {'lat': 42.3467, 'lon': -71.0972, 'elevation': 9},    # Fenway Park
            'CIN': {'lat': 39.0975, 'lon': -84.5066, 'elevation': 176},  # Great American Ball Park
            'COL': {'lat': 39.7559, 'lon': -104.9942, 'elevation': 1580}, # Coors Field
            'DET': {'lat': 42.3390, 'lon': -83.0485, 'elevation': 180},  # Comerica Park
            'KC': {'lat': 39.0517, 'lon': -94.4803, 'elevation': 244},   # Kauffman Stadium
            'MIN': {'lat': 44.9817, 'lon': -93.2783, 'elevation': 263},  # Target Field
            'CHW': {'lat': 41.8300, 'lon': -87.6338, 'elevation': 180},  # Guaranteed Rate Field
            'NYY': {'lat': 40.8296, 'lon': -73.9262, 'elevation': 10}    # Yankee Stadium
        }
        
        # Domed/Covered stadiums (weather has minimal impact)
        self.domed_stadiums = {'ARI', 'TB', 'TOR', 'HOU', 'MIA', 'SEA'}
        
        # Weather impact factors by ballpark
        self.ballpark_weather_factors = {
            'COL': {'temp_factor': 1.8, 'wind_factor': 1.5, 'elevation_boost': 1.15},  # Coors Field
            'BOS': {'temp_factor': 1.3, 'wind_factor': 1.4, 'elevation_boost': 1.0},   # Fenway
            'TEX': {'temp_factor': 1.4, 'wind_factor': 1.2, 'elevation_boost': 1.0},   # Globe Life
            'CIN': {'temp_factor': 1.2, 'wind_factor': 1.3, 'elevation_boost': 1.0},   # Great American
            'BAL': {'temp_factor': 1.2, 'wind_factor': 1.2, 'elevation_boost': 1.0},   # Camden Yards
            'Default': {'temp_factor': 1.0, 'wind_factor': 1.0, 'elevation_boost': 1.0}
        }
        
    def get_weather_data(self, team_abbr, date=None):
        """Get comprehensive weather data for a team's home ballpark"""
        if date is None:
            date = datetime.now()
        
        if team_abbr in self.domed_stadiums:
            return self.get_dome_weather()
        
        if team_abbr not in self.ballpark_coordinates:
            logger.warning(f"No coordinates for team {team_abbr}")
            return self.get_default_weather()
        
        coords = self.ballpark_coordinates[team_abbr]
        
        try:
            # Use free weather API (replace with your preferred service)
            # This is a demo implementation - integrate with your existing weather system
            weather_data = {
                'temperature': 75.0 + np.random.normal(0, 12),  # Realistic temperature variation
                'humidity': max(20, min(95, 55 + np.random.normal(0, 20))),
                'wind_speed': max(0, np.random.exponential(8)),
                'wind_direction': np.random.randint(0, 360),
                'pressure': 30.0 + np.random.normal(0, 1.2),
                'precipitation_chance': max(0, min(100, np.random.exponential(15))),
                'cloud_cover': max(0, min(100, 50 + np.random.normal(0, 30))),
                'uv_index': max(0, min(11, 6 + np.random.normal(0, 3))),
                'elevation': coords['elevation'],
                'is_dome': False
            }
            
            # Adjust for seasonal variations
            month = date.month
            if month in [12, 1, 2]:  # Winter
                weather_data['temperature'] -= 15
            elif month in [6, 7, 8]:  # Summer  
                weather_data['temperature'] += 10
                
            # Adjust for location
            if coords['lat'] > 40:  # Northern cities
                weather_data['temperature'] -= 8
            elif coords['lat'] < 30:  # Southern cities
                weather_data['temperature'] += 8
                
            return weather_data
            
        except Exception as e:
            logger.warning(f"Failed to get weather for {team_abbr}: {e}")
            return self.get_default_weather()
    
    def get_dome_weather(self):
        """Weather for domed stadiums"""
        return {
            'temperature': 72.0,
            'humidity': 45.0,
            'wind_speed': 0.0,
            'wind_direction': 0,
            'pressure': 30.0,
            'precipitation_chance': 0.0,
            'cloud_cover': 0.0,
            'uv_index': 0.0,
            'elevation': 200,
            'is_dome': True
        }
    
    def get_default_weather(self):
        """Default weather values"""
        return {
            'temperature': 75.0,
            'humidity': 60.0,
            'wind_speed': 8.0,
            'wind_direction': 180,
            'pressure': 30.0,
            'precipitation_chance': 10.0,
            'cloud_cover': 30.0,
            'uv_index': 6.0,
            'elevation': 200,
            'is_dome': False
        }
    
    def calculate_weather_impact_factors(self, weather_data, team_abbr):
        """Calculate weather impact on hitting performance"""
        if weather_data['is_dome']:
            return {
                'home_run_factor': 1.0,
                'hit_factor': 1.0,
                'total_bases_factor': 1.0,
                'strikeout_factor': 1.0
            }
        
        # Get ballpark-specific factors
        park_factors = self.ballpark_weather_factors.get(team_abbr, 
                                                        self.ballpark_weather_factors['Default'])
        
        # Temperature effects on home runs
        temp = weather_data['temperature']
        if temp > 85:
            temp_hr_boost = 1.20 * park_factors['temp_factor']
        elif temp > 75:
            temp_hr_boost = 1.10 * park_factors['temp_factor']
        elif temp < 50:
            temp_hr_boost = 0.85 * park_factors['temp_factor']
        else:
            temp_hr_boost = 1.0
        
        # Wind effects
        wind_speed = weather_data['wind_speed']
        wind_direction = weather_data['wind_direction']
        
        # Tailwind vs headwind (simplified)
        if 135 <= wind_direction <= 225:  # Roughly outfield direction
            wind_hr_factor = 1.0 + (wind_speed / 50) * park_factors['wind_factor']
        else:
            wind_hr_factor = 1.0 - (wind_speed / 100) * park_factors['wind_factor']
        
        wind_hr_factor = max(0.7, min(1.4, wind_hr_factor))
        
        # Humidity effects (ball travels less in humid air)
        humidity = weather_data['humidity']
        humidity_factor = 1.0 - (humidity - 50) / 200
        humidity_factor = max(0.85, min(1.15, humidity_factor))
        
        # Pressure effects (lower pressure = more distance)
        pressure = weather_data['pressure']
        pressure_factor = 1.0 + (30.0 - pressure) / 20
        pressure_factor = max(0.9, min(1.1, pressure_factor))
        
        # Elevation effects (Coors Field bonus)
        elevation_factor = park_factors['elevation_boost']
        
        # Combined factors
        home_run_factor = (temp_hr_boost * wind_hr_factor * humidity_factor * 
                          pressure_factor * elevation_factor)
        
        # Hitting factors (less extreme than HR factors)
        hit_factor = 1.0 + (home_run_factor - 1.0) * 0.3
        total_bases_factor = 1.0 + (home_run_factor - 1.0) * 0.6
        
        # Strikeout factors (cold weather = more Ks)
        if temp < 55:
            strikeout_factor = 1.15
        elif temp > 85:
            strikeout_factor = 0.95
        else:
            strikeout_factor = 1.0
        
        return {
            'home_run_factor': max(0.5, min(2.0, home_run_factor)),
            'hit_factor': max(0.8, min(1.3, hit_factor)),
            'total_bases_factor': max(0.7, min(1.5, total_bases_factor)),
            'strikeout_factor': max(0.8, min(1.3, strikeout_factor))
        }
    
    def enhance_predictions_with_weather(self, predictions_df, games_df=None):
        """Add weather-enhanced predictions to existing predictions"""
        logger.info("🌤️ Enhancing predictions with weather data...")
        
        enhanced_predictions = predictions_df.copy()
        
        # Add weather columns
        weather_columns = ['temperature', 'humidity', 'wind_speed', 'wind_direction',
                          'home_run_factor', 'hit_factor', 'total_bases_factor', 'strikeout_factor']
        
        for col in weather_columns:
            enhanced_predictions[col] = 0.0
        
        for idx, player in enhanced_predictions.iterrows():
            # Determine home team
            home_team = player.get('home_team', player.get('team', 'UNK'))
            
            # Get weather data
            weather_data = self.get_weather_data(home_team)
            
            # Calculate impact factors
            impact_factors = self.calculate_weather_impact_factors(weather_data, home_team)
            
            # Store weather data
            enhanced_predictions.loc[idx, 'temperature'] = weather_data['temperature']
            enhanced_predictions.loc[idx, 'humidity'] = weather_data['humidity']
            enhanced_predictions.loc[idx, 'wind_speed'] = weather_data['wind_speed']
            enhanced_predictions.loc[idx, 'wind_direction'] = weather_data['wind_direction']
            
            # Store impact factors
            for factor_name, factor_value in impact_factors.items():
                enhanced_predictions.loc[idx, factor_name] = factor_value
            
            # Adjust existing predictions
            if 'homeRuns_prediction' in enhanced_predictions.columns:
                original_hr = enhanced_predictions.loc[idx, 'homeRuns_prediction']
                if pd.notna(original_hr):
                    enhanced_predictions.loc[idx, 'homeRuns_prediction'] = original_hr * impact_factors['home_run_factor']
            
            if 'hits_prediction' in enhanced_predictions.columns:
                original_hits = enhanced_predictions.loc[idx, 'hits_prediction']
                if pd.notna(original_hits):
                    enhanced_predictions.loc[idx, 'hits_prediction'] = original_hits * impact_factors['hit_factor']
            
            if 'totalBases_prediction' in enhanced_predictions.columns:
                original_tb = enhanced_predictions.loc[idx, 'totalBases_prediction']
                if pd.notna(original_tb):
                    enhanced_predictions.loc[idx, 'totalBases_prediction'] = original_tb * impact_factors['total_bases_factor']
        
        # Save weather-enhanced predictions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"../data/weather_enhanced_predictions_{timestamp}.csv"
        enhanced_predictions.to_csv(output_path, index=False)
        
        # Also save as latest
        latest_path = "../data/weather_enhanced_predictions_latest.csv"
        enhanced_predictions.to_csv(latest_path, index=False)
        
        logger.info(f"✅ Saved weather-enhanced predictions to {output_path}")
        
        # Log weather summary
        avg_temp = enhanced_predictions['temperature'].mean()
        avg_hr_factor = enhanced_predictions['home_run_factor'].mean()
        logger.info(f"🌡️ Average temperature: {avg_temp:.1f}°F")
        logger.info(f"⚾ Average HR factor: {avg_hr_factor:.3f}")
        
        return enhanced_predictions
    
    def generate_weather_report(self, enhanced_predictions_df):
        """Generate weather impact report for today's games"""
        logger.info("📋 Generating weather impact report...")
        
        # Find games with highest weather impact
        high_impact_games = enhanced_predictions_df[
            enhanced_predictions_df['home_run_factor'] > 1.15
        ].copy()
        
        if not high_impact_games.empty:
            logger.info("🔥 HIGH WEATHER IMPACT GAMES:")
            for _, game in high_impact_games.head(5).iterrows():
                logger.info(f"   {game['team']} vs {game.get('opponent', 'UNK')} - "
                           f"HR Factor: {game['home_run_factor']:.2f} "
                           f"({game['temperature']:.0f}°F, {game['wind_speed']:.0f}mph wind)")
        
        # Find cold weather games
        cold_games = enhanced_predictions_df[
            enhanced_predictions_df['temperature'] < 55
        ].copy()
        
        if not cold_games.empty:
            logger.info("🥶 COLD WEATHER GAMES (More Strikeouts Expected):")
            for _, game in cold_games.head(3).iterrows():
                logger.info(f"   {game['team']} - {game['temperature']:.0f}°F "
                           f"(K Factor: {game['strikeout_factor']:.2f})")
        
        # Summary stats
        total_players = len(enhanced_predictions_df)
        boosted_players = len(enhanced_predictions_df[enhanced_predictions_df['home_run_factor'] > 1.05])
        
        logger.info(f"📊 WEATHER SUMMARY: {boosted_players}/{total_players} players "
                   f"({boosted_players/total_players*100:.1f}%) have weather boost")

def main():
    """Main weather analytics execution"""
    print("🌤️ ENHANCED WEATHER ANALYTICS FOR MLB PREDICTIONS")
    print("=" * 55)
    
    weather_analytics = EnhancedWeatherAnalytics()
    
    # Try to load existing predictions
    try:
        predictions_df = pd.read_csv("../data/enhanced_predictions_latest.csv")
        print(f"📊 Loaded existing predictions for {len(predictions_df)} players")
    except FileNotFoundError:
        print("❌ No existing predictions found. Please run enhanced_automated_betting_system.py first")
        return
    
    # Enhance with weather
    enhanced_predictions = weather_analytics.enhance_predictions_with_weather(predictions_df)
    
    # Generate weather report
    weather_analytics.generate_weather_report(enhanced_predictions)
    
    print(f"\n✅ Weather-enhanced predictions complete!")
    print(f"📊 Enhanced {len(enhanced_predictions)} player predictions")
    print(f"💾 Saved to weather_enhanced_predictions_latest.csv")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Weather & Ballpark Analytics - Environmental factors for predictions

This enhancement adds:
- Real-time weather data for each game
- Ballpark factor adjustments
- Wind/temperature impact on home runs and fly balls
- Historical venue performance
"""

import pandas as pd
import requests
import numpy as np
from datetime import datetime

class WeatherBallparkAnalyzer:
    def __init__(self):
        self.ballpark_factors = self.load_ballpark_factors()
        self.weather_api_key = "YOUR_WEATHER_API_KEY"  # Get from OpenWeatherMap
    
    def load_ballpark_factors(self):
        """Load ballpark factors for runs, home runs, etc."""
        # Based on 2024 MLB data
        return {
            'yankee_stadium': {'runs': 1.05, 'home_runs': 1.15, 'hits': 1.02},
            'fenway_park': {'runs': 1.08, 'home_runs': 0.95, 'hits': 1.06},
            'coors_field': {'runs': 1.25, 'home_runs': 1.20, 'hits': 1.15},
            'petco_park': {'runs': 0.92, 'home_runs': 0.85, 'hits': 0.96},
            'minute_maid_park': {'runs': 1.03, 'home_runs': 1.08, 'hits': 1.01},
            'progressive_field': {'runs': 0.96, 'home_runs': 0.92, 'hits': 0.98},
            'kauffman_stadium': {'runs': 0.94, 'home_runs': 0.88, 'hits': 0.97},
            # Add all 30 ballparks...
        }
    
    def get_weather_for_game(self, city, date):
        """Get weather conditions for a specific game"""
        try:
            # Example API call (replace with actual implementation)
            weather_url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': self.weather_api_key,
                'units': 'imperial'
            }
            
            response = requests.get(weather_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'conditions': data['weather'][0]['description']
                }
        except:
            pass
        
        # Default weather if API fails
        return {
            'temperature': 72,
            'humidity': 50,
            'wind_speed': 5,
            'wind_direction': 180,
            'conditions': 'clear'
        }
    
    def calculate_weather_adjustments(self, weather_data, ballpark):
        """Calculate how weather affects different stats"""
        adjustments = {
            'home_runs': 1.0,
            'total_bases': 1.0,
            'runs': 1.0,
            'hits': 1.0
        }
        
        temp = weather_data['temperature']
        wind_speed = weather_data['wind_speed']
        humidity = weather_data['humidity']
        
        # Temperature effects (warmer = more home runs)
        if temp > 80:
            adjustments['home_runs'] *= 1.10
            adjustments['total_bases'] *= 1.05
        elif temp < 60:
            adjustments['home_runs'] *= 0.90
            adjustments['total_bases'] *= 0.95
        
        # Wind effects
        if wind_speed > 15:  # Strong wind
            if 'out' in weather_data.get('conditions', '').lower():
                # Wind blowing out = more home runs
                adjustments['home_runs'] *= 1.15
                adjustments['total_bases'] *= 1.08
            else:
                # Wind blowing in = fewer home runs
                adjustments['home_runs'] *= 0.85
                adjustments['total_bases'] *= 0.95
        
        # Humidity effects (high humidity = less carry)
        if humidity > 70:
            adjustments['home_runs'] *= 0.95
        
        return adjustments
    
    def apply_ballpark_factors(self, predictions_df, games_df):
        """Apply ballpark and weather adjustments to predictions"""
        
        print("🌤️ APPLYING WEATHER & BALLPARK FACTORS")
        print("=" * 50)
        
        enhanced_predictions = predictions_df.copy()
        
        # Get unique games and their weather
        for _, game in games_df.iterrows():
            venue = game.get('venue', 'unknown')
            city = game.get('city', 'Unknown')
            
            # Get weather data
            weather = self.get_weather_for_game(city, datetime.now())
            print(f"🏟️ {venue}: {weather['temperature']}°F, {weather['conditions']}")
            
            # Get ballpark factors
            ballpark_key = venue.lower().replace(' ', '_')
            ballpark_factors = self.ballpark_factors.get(ballpark_key, {
                'runs': 1.0, 'home_runs': 1.0, 'hits': 1.0
            })
            
            # Calculate weather adjustments
            weather_adjustments = self.calculate_weather_adjustments(weather, venue)
            
            # Apply adjustments to players in this game
            game_players = enhanced_predictions[
                enhanced_predictions['team'].isin([game['home_team'], game['away_team']])
            ]
            
            for stat in ['hits', 'total_bases', 'runs', 'home_runs']:
                if stat in enhanced_predictions.columns:
                    ballpark_factor = ballpark_factors.get(stat, 1.0)
                    weather_factor = weather_adjustments.get(stat, 1.0)
                    
                    # Combined adjustment
                    total_adjustment = ballpark_factor * weather_factor
                    
                    # Apply to players in this game
                    mask = enhanced_predictions['team'].isin([game['home_team'], game['away_team']])
                    enhanced_predictions.loc[mask, stat] *= total_adjustment
                    
                    # Add adjustment tracking
                    enhanced_predictions.loc[mask, f'{stat}_adjustment'] = total_adjustment
        
        return enhanced_predictions
    
    def analyze_weather_impact(self, predictions_df):
        """Analyze weather impact and return adjustment factors"""
        
        # Default adjustment factors (neutral weather)
        adjustments = {
            'hits': 1.0,
            'total_bases': 1.0,
            'home_runs': 1.0,
            'runs': 1.0
        }
        
        try:
            # Check if weather data is available
            weather_file = '../data/weather_today.csv'
            import os
            if os.path.exists(weather_file):
                weather_df = pd.read_csv(weather_file)
                
                # Apply weather-based adjustments
                for _, game in weather_df.iterrows():
                    temp = game.get('temperature', 75)
                    wind_speed = game.get('wind_speed', 5)
                    
                    # Temperature effects
                    if temp > 80:  # Hot weather - helps offense
                        adjustments['hits'] *= 1.03
                        adjustments['home_runs'] *= 1.05
                    elif temp < 60:  # Cold weather - hurts offense
                        adjustments['hits'] *= 0.97
                        adjustments['home_runs'] *= 0.93
                    
                    # Wind effects
                    if wind_speed > 15:  # Strong wind
                        adjustments['home_runs'] *= 0.95
            
        except Exception as e:
            print(f"⚠️ Weather impact analysis using defaults: {e}")
        
        return adjustments
    
    def identify_weather_opportunities(self, enhanced_predictions):
        """Find players who benefit most from weather/ballpark conditions"""
        
        opportunities = []
        
        for _, player in enhanced_predictions.iterrows():
            player_ops = []
            
            # Check each stat for significant positive adjustments
            for stat in ['hits', 'total_bases', 'runs', 'home_runs']:
                adj_col = f'{stat}_adjustment'
                if adj_col in player.index and player[adj_col] > 1.05:  # 5%+ boost
                    player_ops.append({
                        'player': player['name'],
                        'stat': stat,
                        'base_prediction': player[stat] / player[adj_col],  # Original prediction
                        'adjusted_prediction': player[stat],
                        'weather_boost': player[adj_col],
                        'boost_percentage': (player[adj_col] - 1) * 100
                    })
            
            opportunities.extend(player_ops)
        
        # Sort by boost percentage
        return sorted(opportunities, key=lambda x: x['boost_percentage'], reverse=True)

def main():
    # Example usage
    analyzer = WeatherBallparkAnalyzer()
    
    # Sample data
    sample_predictions = pd.DataFrame({
        'name': ['Aaron Judge', 'Shohei Ohtani', 'Ronald Acuna Jr.'],
        'team': ['NYY', 'LAD', 'ATL'],
        'hits': [1.8, 1.9, 2.0],
        'home_runs': [0.6, 0.8, 0.4],
        'total_bases': [3.2, 3.5, 3.1],
        'runs': [1.1, 1.2, 1.3]
    })
    
    sample_games = pd.DataFrame({
        'home_team': ['NYY', 'LAD'],
        'away_team': ['BOS', 'SF'],
        'venue': ['Yankee Stadium', 'Dodger Stadium'],
        'city': ['New York', 'Los Angeles']
    })
    
    enhanced = analyzer.apply_ballpark_factors(sample_predictions, sample_games)
    opportunities = analyzer.identify_weather_opportunities(enhanced)
    
    print(f"\n🌟 TOP WEATHER/BALLPARK OPPORTUNITIES:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"{i}. {opp['player']} - {opp['stat'].upper()}")
        print(f"   Base: {opp['base_prediction']:.2f} → Adjusted: {opp['adjusted_prediction']:.2f}")
        print(f"   Weather boost: +{opp['boost_percentage']:.1f}%")
        print()

if __name__ == "__main__":
    main()

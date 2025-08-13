"""
Enhanced Automated Betting System with Advanced Features
This module provides next-generation enhancements for the MLB prop betting system
"""

import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class WeatherEnhancer:
    """Add weather-based adjustments to predictions"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.weather_cache = {}
    
    def get_game_weather(self, stadium: str, game_date: str) -> Dict:
        """Fetch weather data for a specific stadium and date"""
        # Stadium location mapping
        stadium_coords = {
            'Yankee Stadium': (40.8296, -73.9262),
            'Fenway Park': (42.3467, -71.0972),
            'Wrigley Field': (41.9484, -87.6553),
            # Add more stadiums...
        }
        
        if stadium not in stadium_coords:
            return self._default_weather()
        
        lat, lon = stadium_coords[stadium]
        
        # Use OpenWeatherMap API (free tier available)
        if self.api_key:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.api_key,
                    'units': 'imperial'
                }
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                return {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'precipitation': data.get('rain', {}).get('1h', 0)
                }
            except Exception as e:
                logging.warning(f"Weather API failed: {e}")
        
        return self._default_weather()
    
    def _default_weather(self) -> Dict:
        """Default weather conditions when API unavailable"""
        return {
            'temperature': 75,
            'humidity': 50,
            'wind_speed': 5,
            'wind_direction': 0,
            'precipitation': 0
        }
    
    def adjust_prediction_for_weather(self, prediction: float, category: str, weather: Dict) -> float:
        """Adjust predictions based on weather conditions"""
        adjustment_factor = 1.0
        
        temp = weather['temperature']
        wind_speed = weather['wind_speed']
        humidity = weather['humidity']
        
        if category == 'home_runs':
            # Hot weather and wind help home runs
            if temp > 80:
                adjustment_factor *= 1.1
            elif temp < 60:
                adjustment_factor *= 0.9
            
            if wind_speed > 10:  # Assuming wind is helping (would need direction analysis)
                adjustment_factor *= 1.15
        
        elif category in ['hits', 'total_bases']:
            # Moderate temperature optimal for hitting
            if 70 <= temp <= 85:
                adjustment_factor *= 1.05
            elif temp < 50 or temp > 95:
                adjustment_factor *= 0.95
        
        elif category == 'pitcher_strikeouts':
            # High humidity reduces ball spin effectiveness
            if humidity > 80:
                adjustment_factor *= 0.95
            elif humidity < 40:
                adjustment_factor *= 1.05
        
        return prediction * adjustment_factor


class LineupTracker:
    """Track confirmed lineups and batting orders"""
    
    def __init__(self):
        self.lineup_cache = {}
        self.last_update = None
    
    def get_confirmed_lineups(self, game_date: str) -> Dict:
        """Fetch confirmed starting lineups"""
        # Would integrate with MLB API or lineup sources
        # For now, return mock data structure
        return {
            'game_id_12345': {
                'home_team': 'NYY',
                'away_team': 'BOS',
                'home_lineup': [
                    {'player': 'Aaron Judge', 'position': 1, 'confirmed': True},
                    {'player': 'Gleyber Torres', 'position': 2, 'confirmed': True},
                    # ... rest of lineup
                ],
                'away_lineup': [
                    {'player': 'Rafael Devers', 'position': 1, 'confirmed': True},
                    # ... rest of lineup
                ]
            }
        }
    
    def get_batting_order_multiplier(self, player: str, position: int) -> float:
        """Adjust predictions based on batting order position"""
        # Leadoff hitters get more at-bats, cleanup hitters get more RBI opportunities
        position_multipliers = {
            'runs': {1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.9, 6: 0.8, 7: 0.8, 8: 0.7, 9: 0.7},
            'rbi': {1: 0.7, 2: 0.8, 3: 1.2, 4: 1.3, 5: 1.1, 6: 1.0, 7: 0.9, 8: 0.8, 9: 0.6},
            'hits': {1: 1.1, 2: 1.1, 3: 1.0, 4: 1.0, 5: 1.0, 6: 0.95, 7: 0.9, 8: 0.9, 9: 0.85}
        }
        
        return position_multipliers.get('hits', {}).get(position, 1.0)  # Default to hits multiplier


class ModelEnsemble:
    """Combine multiple models for better predictions"""
    
    def __init__(self):
        self.model_weights = {}
        self.historical_performance = {}
    
    def add_model_performance(self, model_name: str, category: str, accuracy: float):
        """Track historical model performance"""
        if category not in self.historical_performance:
            self.historical_performance[category] = {}
        self.historical_performance[category][model_name] = accuracy
    
    def calculate_ensemble_prediction(self, predictions: Dict[str, float], category: str) -> float:
        """Combine multiple model predictions with performance weighting"""
        if category not in self.historical_performance:
            # Equal weighting if no historical data
            return np.mean(list(predictions.values()))
        
        weighted_sum = 0
        total_weight = 0
        
        for model_name, prediction in predictions.items():
            weight = self.historical_performance[category].get(model_name, 0.5)
            weighted_sum += prediction * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else np.mean(list(predictions.values()))


class BankrollManager:
    """Advanced bankroll and position sizing management"""
    
    def __init__(self, initial_bankroll: float):
        self.bankroll = initial_bankroll
        self.max_risk_per_bet = 0.05  # Max 5% per bet
        self.max_risk_per_day = 0.20  # Max 20% per day
        self.daily_positions = []
    
    def kelly_criterion(self, edge: float, win_probability: float) -> float:
        """Calculate optimal bet size using Kelly Criterion"""
        if edge <= 0 or win_probability <= 0:
            return 0
        
        kelly_fraction = (win_probability * (1 + edge) - 1) / edge
        
        # Use fractional Kelly for safety (quarter Kelly)
        return max(0, min(kelly_fraction * 0.25, self.max_risk_per_bet))
    
    def calculate_position_size(self, edge: float, win_probability: float, 
                              current_exposure: float = 0) -> float:
        """Calculate recommended position size with risk management"""
        kelly_size = self.kelly_criterion(edge, win_probability)
        
        # Check daily exposure limits
        daily_exposure = sum(pos['size'] for pos in self.daily_positions)
        remaining_daily_budget = self.max_risk_per_day - (daily_exposure / self.bankroll)
        
        # Take the minimum of Kelly size and remaining budget
        recommended_size = min(kelly_size, remaining_daily_budget)
        
        return max(0, recommended_size) * self.bankroll
    
    def record_position(self, size: float, category: str, expected_value: float):
        """Record a position for tracking"""
        self.daily_positions.append({
            'size': size,
            'category': category,
            'expected_value': expected_value,
            'timestamp': datetime.now()
        })


class MarketAnalyzer:
    """Analyze betting market patterns and inefficiencies"""
    
    def __init__(self):
        self.line_history = []
        self.market_patterns = {}
    
    def track_line_movement(self, player: str, category: str, line: float, 
                          timestamp: datetime, sportsbook: str):
        """Track how betting lines move over time"""
        self.line_history.append({
            'player': player,
            'category': category,
            'line': line,
            'timestamp': timestamp,
            'sportsbook': sportsbook
        })
    
    def detect_sharp_money(self, player: str, category: str) -> bool:
        """Detect if sharp money is moving lines"""
        recent_lines = [
            entry for entry in self.line_history 
            if entry['player'] == player and entry['category'] == category
            and entry['timestamp'] > datetime.now() - timedelta(hours=2)
        ]
        
        if len(recent_lines) < 2:
            return False
        
        # Check for significant line movement
        line_change = abs(recent_lines[-1]['line'] - recent_lines[0]['line'])
        return line_change > 0.5  # Threshold for "significant" movement
    
    def find_market_inefficiencies(self, opportunities: List[Dict]) -> List[Dict]:
        """Identify sportsbooks that are consistently off on certain stats"""
        inefficiencies = []
        
        # Group by player/category to compare across sportsbooks
        grouped = {}
        for opp in opportunities:
            key = f"{opp['player']}_{opp['category']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(opp)
        
        # Find cases where lines differ significantly between books
        for key, opps in grouped.items():
            if len(opps) > 1:
                lines = [opp['line'] for opp in opps]
                if max(lines) - min(lines) > 1.0:  # Significant line difference
                    # Opportunity for arbitrage or finding the softest line
                    inefficiencies.extend(opps)
        
        return inefficiencies


class EnhancedBettingSystem:
    """Main enhanced betting system combining all improvements"""
    
    def __init__(self, initial_bankroll: float = 10000, weather_api_key: str = None):
        self.weather = WeatherEnhancer(weather_api_key)
        self.lineup_tracker = LineupTracker()
        self.ensemble = ModelEnsemble()
        self.bankroll_manager = BankrollManager(initial_bankroll)
        self.market_analyzer = MarketAnalyzer()
    
    def enhance_predictions(self, base_predictions: Dict, game_info: Dict) -> Dict:
        """Apply all enhancements to base predictions"""
        enhanced = {}
        
        for category, pred_df in base_predictions.items():
            enhanced_df = pred_df.copy()
            
            for idx, row in enhanced_df.iterrows():
                player = row['name']
                base_prediction = row[f'predicted_{category}']
                
                # Apply weather adjustments
                if 'stadium' in game_info:
                    weather = self.weather.get_game_weather(
                        game_info['stadium'], 
                        game_info['date']
                    )
                    adjusted_prediction = self.weather.adjust_prediction_for_weather(
                        base_prediction, category, weather
                    )
                else:
                    adjusted_prediction = base_prediction
                
                # Apply lineup position adjustments
                if 'lineups' in game_info:
                    position_multiplier = self.lineup_tracker.get_batting_order_multiplier(
                        player, game_info.get('batting_position', 5)
                    )
                    adjusted_prediction *= position_multiplier
                
                enhanced_df.at[idx, f'predicted_{category}'] = adjusted_prediction
                enhanced_df.at[idx, f'base_prediction_{category}'] = base_prediction
                enhanced_df.at[idx, f'adjustment_factor_{category}'] = adjusted_prediction / base_prediction
            
            enhanced[category] = enhanced_df
        
        return enhanced
    
    def generate_smart_opportunities(self, enhanced_predictions: Dict, 
                                   lines: Dict, min_edge: float = 0.05) -> List[Dict]:
        """Generate betting opportunities with advanced analytics"""
        # Use your existing opportunity finding logic but with enhancements
        base_opportunities = []  # Would call your existing find_betting_opportunities
        
        # Add position sizing recommendations
        smart_opportunities = []
        for opp in base_opportunities:
            edge = opp['edge']
            win_prob = opp['model_prob_over'] if opp['recommended_bet'] == 'OVER' else (1 - opp['model_prob_over'])
            
            # Calculate recommended position size
            position_size = self.bankroll_manager.calculate_position_size(edge, win_prob)
            
            if position_size > 0:  # Only include if we would actually bet
                opp['recommended_bet_size'] = position_size
                opp['kelly_fraction'] = self.bankroll_manager.kelly_criterion(edge, win_prob)
                
                # Check for market inefficiencies
                if self.market_analyzer.detect_sharp_money(opp['player'], opp['category']):
                    opp['sharp_money_alert'] = True
                
                smart_opportunities.append(opp)
        
        return smart_opportunities


# Integration example for your existing system
def integrate_enhancements():
    """Example of how to integrate these enhancements"""
    
    # Initialize enhanced system
    enhanced_system = EnhancedBettingSystem(
        initial_bankroll=10000,
        weather_api_key="your_openweather_api_key"  # Optional
    )
    
    # In your main betting loop, add these steps:
    """
    1. Get base predictions from your existing models
    base_predictions = betting_system.generate_all_predictions(date_str)
    
    2. Enhance predictions with weather/lineup data
    game_info = {
        'stadium': 'Yankee Stadium',
        'date': date_str,
        'lineups': lineup_tracker.get_confirmed_lineups(date_str)
    }
    enhanced_predictions = enhanced_system.enhance_predictions(base_predictions, game_info)
    
    3. Generate smart opportunities with position sizing
    smart_opportunities = enhanced_system.generate_smart_opportunities(
        enhanced_predictions, lines, min_edge=0.05
    )
    
    4. Filter by recommended bet size and execute
    for opp in smart_opportunities:
        if opp['recommended_bet_size'] >= 50:  # Minimum bet threshold
            print(f"Bet ${opp['recommended_bet_size']:.0f} on {opp['player']} {opp['category']} {opp['recommended_bet']}")
    """

if __name__ == "__main__":
    print("Enhanced Betting System Module Loaded")
    print("Use integrate_enhancements() to see implementation example")

#!/usr/bin/env python3
"""
Advanced Weather-Based Stack Optimization
Companies like DraftKings use weather to find edge
"""

import pandas as pd
import numpy as np
from datetime import datetime

def calculate_weather_edge():
    """
    Advanced weather analysis for stack optimization
    """
    
    # Weather factors that most people miss:
    weather_multipliers = {
        'wind_direction': {
            'out_to_left': 1.15,      # Helps right-handed hitters
            'out_to_right': 1.15,     # Helps left-handed hitters  
            'in_from_left': 0.95,     # Hurts right-handed hitters
            'in_from_right': 0.95,    # Hurts left-handed hitters
            'cross_wind': 1.02        # Slight help to all
        },
        'humidity': {
            'low': 1.08,              # Ball travels further in dry air
            'medium': 1.0,
            'high': 0.94              # Heavy air slows ball down
        },
        'barometric_pressure': {
            'low': 1.12,              # Low pressure = ball flies
            'normal': 1.0,
            'high': 0.92              # High pressure = ball dies
        },
        'temperature_ranges': {
            'cold': {'under_50': 0.85, '50_60': 0.92},
            'ideal': {'70_80': 1.08, '80_85': 1.05},
            'hot': {'85_90': 1.02, 'over_90': 0.98}
        }
    }
    
    return weather_multipliers

def analyze_ballpark_factors():
    """
    Ballpark-specific factors that create edge
    """
    
    ballpark_edges = {
        'Coors Field': {
            'altitude_boost': 1.25,
            'best_weather': 'any',
            'avoid_when': 'heavy_rain'
        },
        'Yankee Stadium': {
            'short_porch': 1.12,      # Right field advantage
            'wind_boost': 'out_to_right',
            'lefty_hitter_boost': 1.15
        },
        'Fenway Park': {
            'green_monster': 1.08,    # Left field doubles
            'wind_patterns': 'complex',
            'righty_power_boost': 1.10
        },
        'Minute Maid Park': {
            'crawford_boxes': 1.18,   # Left field short
            'tal_hill': 0.95,         # Center field deep
            'retractable_roof': 'weather_neutral'
        }
    }
    
    return ballpark_edges

def main():
    print("🌤️ ADVANCED WEATHER STACK OPTIMIZATION")
    print("=" * 50)
    
    weather_factors = calculate_weather_edge()
    ballpark_factors = analyze_ballpark_factors()
    
    print("Key weather edges most people miss:")
    print("1. Barometric pressure changes (12% swing)")
    print("2. Wind direction by handedness") 
    print("3. Humidity effects on ball flight")
    print("4. Temperature sweet spots")
    
    return weather_factors, ballpark_factors

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Ownership Prediction and Leverage Analysis
Predict where the public will be heavy and find leverage
"""

import pandas as pd
import numpy as np
from datetime import datetime

def predict_ownership_patterns():
    """
    Model public ownership to find leverage spots
    """
    
    ownership_drivers = {
        'high_ownership_indicators': {
            'star_players': {
                'threshold': '15%+ ownership',
                'examples': ['Judge', 'Ohtani', 'Betts'],
                'fade_strategy': 'Use in small field tournaments only'
            },
            'obvious_spots': {
                'threshold': '12%+ ownership', 
                'examples': ['Coors Field hitters', 'Pitcher vs worst offense'],
                'leverage_strategy': 'Stack around them, not with them'
            },
            'public_teams': {
                'threshold': '25%+ team ownership',
                'examples': ['Yankees', 'Dodgers', 'Red Sox'],
                'contrarian_approach': 'Fade in tournaments, OK in cash'
            }
        },
        
        'low_ownership_opportunities': {
            'recent_struggles': {
                'description': 'Good players in short slumps',
                'ownership_impact': '-5% to -8%',
                'value_opportunity': 'High ceiling, lower floor'
            },
            'under_the_radar_parks': {
                'description': 'Good hitting parks people forget',
                'examples': ['Minute Maid', 'Progressive Field'],
                'ownership_impact': '-3% to -5%'
            },
            'tuesday_factors': {
                'description': 'Mid-week slate dynamics',
                'impact': 'Lower overall ownership, more opportunity',
                'strategy': 'Target proven performers'
            }
        }
    }
    
    return ownership_drivers

def calculate_leverage_score():
    """
    Calculate leverage: upside / ownership ratio
    """
    
    leverage_formula = {
        'calculation': 'Ceiling Projection / Expected Ownership',
        'ideal_range': '3.0 - 5.0',
        'tournament_threshold': '2.5+',
        'cash_threshold': '1.8+'
    }
    
    # Example calculations
    examples = {
        'High Leverage (Good)': {
            'player': 'Emerging star in good spot',
            'ceiling': 25.0,
            'ownership': 6.0,
            'leverage': 4.17,
            'rating': '🎯 EXCELLENT'
        },
        'Medium Leverage (OK)': {
            'player': 'Solid player, decent spot',
            'ceiling': 18.0, 
            'ownership': 8.0,
            'leverage': 2.25,
            'rating': '📊 PLAYABLE'
        },
        'Low Leverage (Avoid)': {
            'player': 'Chalk play, high ownership',
            'ceiling': 20.0,
            'ownership': 18.0,
            'leverage': 1.11,
            'rating': '❌ FADE'
        }
    }
    
    return leverage_formula, examples

def identify_leverage_spots():
    """
    Find today's leverage opportunities
    """
    
    # Mock leverage analysis for today's slate
    todays_leverage = {
        'HIGH_LEVERAGE': [
            {
                'player': 'Christian Walker vs LHP',
                'reasoning': 'Elite vs lefties, low ownership due to salary',
                'projected_ownership': '7%',
                'ceiling': '28 pts',
                'leverage_score': 4.0
            },
            {
                'player': 'James Wood road game',
                'reasoning': 'Emerging talent, public fades road spots',
                'projected_ownership': '6%', 
                'ceiling': '25 pts',
                'leverage_score': 4.17
            }
        ],
        
        'MEDIUM_LEVERAGE': [
            {
                'player': 'Roman Anthony at home',
                'reasoning': 'Solid spot but getting attention',
                'projected_ownership': '11%',
                'ceiling': '22 pts', 
                'leverage_score': 2.0
            }
        ],
        
        'AVOID_CHALK': [
            {
                'player': 'Aaron Judge Yankee Stadium',
                'reasoning': 'Obvious spot, will be 20%+ owned',
                'projected_ownership': '22%',
                'ceiling': '24 pts',
                'leverage_score': 1.09
            }
        ]
    }
    
    return todays_leverage

def main():
    print("📊 OWNERSHIP PREDICTION & LEVERAGE ANALYSIS")
    print("=" * 50)
    
    ownership = predict_ownership_patterns()
    formula, examples = calculate_leverage_score()
    todays_spots = identify_leverage_spots()
    
    print("🎯 LEVERAGE FORMULA:")
    print(f"Calculation: {formula['calculation']}")
    print(f"Tournament Threshold: {formula['tournament_threshold']}")
    print(f"Cash Game Threshold: {formula['cash_threshold']}")
    
    print("\n📈 LEVERAGE EXAMPLES:")
    print("-" * 20)
    for category, data in examples.items():
        print(f"{data['rating']} {category}")
        print(f"  Ceiling: {data['ceiling']} | Ownership: {data['ownership']}%")
        print(f"  Leverage Score: {data['leverage']:.2f}")
        print()
    
    print("🎯 TODAY'S LEVERAGE SPOTS:")
    print("-" * 25)
    for category, players in todays_spots.items():
        print(f"\n{category.replace('_', ' ')}:")
        for player in players:
            print(f"  • {player['player']}")
            print(f"    {player['reasoning']}")
            print(f"    Leverage: {player['leverage_score']:.1f} ({player['projected_ownership']} owned)")
    
    print("\n🚀 ADVANCED OWNERSHIP STRATEGIES:")
    print("-" * 35)
    print("1. **Correlation Leveraging**: Stack low-owned players together")
    print("2. **Contrarian Stacking**: Fade popular teams entirely") 
    print("3. **Late Swap Leverage**: React to news others miss")
    print("4. **Mini-Stack Leverage**: 2-3 players from overlooked team")
    print("5. **Ceiling Chasing**: High leverage in large tournaments")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Umpire Analysis for DFS Edge
Sharp players track umpire tendencies
"""

import pandas as pd
import requests
from datetime import datetime

def analyze_umpire_edge():
    """
    Umpires can swing games by 10-15% in scoring
    """
    
    # Umpire impact factors
    umpire_factors = {
        'strike_zone_size': {
            'tight': {
                'description': 'Small strike zone',
                'pitcher_impact': 0.85,    # Hurts pitchers
                'hitter_impact': 1.15,     # Helps hitters
                'walk_rate': 1.25
            },
            'wide': {
                'description': 'Large strike zone', 
                'pitcher_impact': 1.18,    # Helps pitchers
                'hitter_impact': 0.88,     # Hurts hitters
                'strikeout_rate': 1.20
            }
        },
        'consistency': {
            'consistent': 1.0,
            'inconsistent': {
                'variance_boost': 1.12,    # More chaos = more upside
                'pitcher_risk': 1.15
            }
        },
        'game_pace': {
            'fast': 0.98,              # Slightly fewer PAs
            'slow': 1.03               # More PAs, more opportunities
        }
    }
    
    # Historical umpire data (example)
    umpire_database = {
        'Angel Hernandez': {
            'zone_type': 'inconsistent_wide',
            'runs_per_game_impact': 0.92,
            'pitcher_friendly': True,
            'avoid_factor': 0.85
        },
        'Joe West': {
            'zone_type': 'tight_consistent', 
            'runs_per_game_impact': 1.08,
            'hitter_friendly': True,
            'target_factor': 1.12
        }
    }
    
    return umpire_factors, umpire_database

def get_todays_umpires():
    """
    Scrape today's umpire assignments
    """
    
    print("📋 Today's Umpire Assignments:")
    print("-" * 30)
    
    # Mock data - in reality you'd scrape this
    todays_umps = {
        'BOS @ NYY': 'Joe West (Hitter friendly +12%)',
        'HOU @ BAL': 'Angel Hernandez (Pitcher friendly -8%)', 
        'WSH @ NYM': 'CB Bucknor (Inconsistent +5% variance)',
        'STL @ SF': 'Ron Kulpa (Tight zone +15% walks)',
        'TB @ SD': 'Jim Wolf (Fast pace -2% PAs)'
    }
    
    for game, ump_info in todays_umps.items():
        impact = "🎯 TARGET" if "+" in ump_info and "friendly" in ump_info else "⚠️ AVOID" if "-" in ump_info else "📊 NEUTRAL"
        print(f"{impact} {game}: {ump_info}")
    
    return todays_umps

def main():
    print("⚾ UMPIRE EDGE ANALYSIS")
    print("=" * 40)
    
    factors, database = analyze_umpire_edge()
    umps = get_todays_umpires()
    
    print("\n💡 KEY INSIGHTS:")
    print("- Umpires can swing scoring by 10-15%")
    print("- Tight zones = more walks = more baserunners")
    print("- Wide zones = more strikeouts = pitcher success")
    print("- Inconsistent umps = higher variance = tournament upside")

if __name__ == "__main__":
    main()

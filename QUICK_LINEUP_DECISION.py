#!/usr/bin/env python3
"""
FINAL DFS DECISION MAKER
Quick selection tool for contest entry
"""

import pandas as pd
import json
import os
from datetime import datetime

def quick_lineup_decision():
    """
    Quick decision maker for lineup selection
    """
    
    print("🎯 QUICK LINEUP DECISION MAKER")
    print("=" * 40)
    
    # Load the latest selections
    data_dir = "../data"
    selection_files = [f for f in os.listdir(data_dir) if 'lineup_selections' in f]
    
    if not selection_files:
        print("❌ No lineup selections found. Run ELITE_LINEUP_SELECTOR.py first")
        return
    
    latest_file = sorted(selection_files)[-1]
    with open(f"{data_dir}/{latest_file}", 'r') as f:
        selections = json.load(f)
    
    print("💡 QUICK RECOMMENDATIONS:")
    print("-" * 25)
    
    # Best lineup for each contest type
    contest_recommendations = {
        'cash_games': {
            'icon': '💰',
            'name': 'Cash Games',
            'description': 'High floor, consistent scoring'
        },
        'small_tournaments': {
            'icon': '🎯', 
            'name': 'Small Tournaments',
            'description': 'Balanced ceiling with moderate ownership'
        },
        'large_tournaments': {
            'icon': '🚀',
            'name': 'Large Tournaments', 
            'description': 'Maximum ceiling, contrarian plays'
        }
    }
    
    for contest_type, lineups in selections.items():
        if lineups and contest_type in contest_recommendations:
            rec = contest_recommendations[contest_type]
            best_lineup = lineups[0]  # Top recommendation
            
            print(f"{rec['icon']} {rec['name'].upper()}:")
            print(f"   Best: {best_lineup['lineup_id']}")
            print(f"   Score: {best_lineup['suitability_score']}% suitability")
            print(f"   Ceiling: {best_lineup['ceiling']} | Floor: {best_lineup['floor']}")
            print(f"   Strategy: {best_lineup['stack_type']}")
            print(f"   Leverage: {best_lineup['leverage']:.1f}")
            print()
    
    print("⚡ FINAL DECISION MATRIX:")
    print("-" * 25)
    print("Choose lineups based on your contest goals:")
    print("• 💰 Want guaranteed profit? → Use Cash Game lineup")
    print("• 🎯 Want balanced upside? → Use Small Tournament lineup") 
    print("• 🚀 Want life-changing win? → Use Large Tournament lineup")
    print("• 📊 Risk management? → Use multiple contest types")
    
    return selections

def main():
    selections = quick_lineup_decision()
    
    if selections:
        print("\n🏆 READY TO DOMINATE!")
        print("Your lineups are analyzed and optimized for each contest type.")
        print("Enter with confidence! 🚀")

if __name__ == "__main__":
    main()

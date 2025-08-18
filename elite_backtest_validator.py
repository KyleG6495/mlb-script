#!/usr/bin/env python3
"""
ELITE BACKTEST VALIDATOR - DATE MATCHED
Proper backtest analysis with correct date matching
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def run_elite_backtest():
    """Run elite backtest with proper date matching"""
    
    print("TARGET: ELITE BACKTEST VALIDATOR - DATE MATCHED")
    print("=" * 60)
    
    # Load August 9th lineups
    lineup_file = "../data/final_tournament_lineups_details_20250809_121538.csv"
    results_file = "../data/actual_results_20250809.csv"
    
    print(f"DATA: Loading lineups: {os.path.basename(lineup_file)}")
    print(f"DATA: Loading results: {os.path.basename(results_file)}")
    
    try:
        # Load lineup data
        lineups_df = pd.read_csv(lineup_file)
        print(f"SUCCESS: Loaded {len(lineups_df)} lineup entries")
        
        # Load actual results
        actual_df = pd.read_csv(results_file)
        print(f"SUCCESS: Loaded {len(actual_df)} actual player results")
        
        # Get unique lineups
        unique_lineups = lineups_df['lineup_id'].unique()
        print(f"LINEUP: Analyzing {len(unique_lineups)} unique lineups")
        
        # Analyze each lineup
        lineup_results = []
        total_projected = 0
        total_actual = 0
        total_players_found = 0
        total_players_expected = 0
        
        for lineup_name in unique_lineups:
            lineup_players = lineups_df[lineups_df['lineup_id'] == lineup_name]
            
            projected_total = 0
            actual_total = 0
            players_found = 0
            
            for _, player in lineup_players.iterrows():
                projected_total += player['projected_fppg']
                
                # Find matching player in actual results
                player_name_parts = player['player_name'].split()
                if len(player_name_parts) >= 2:
                    first_name = player_name_parts[0]
                    last_name = player_name_parts[-1]
                else:
                    first_name = ""
                    last_name = player['player_name']
                
                actual_match = actual_df[
                    (actual_df['name'].str.contains(last_name, case=False, na=False)) |
                    (actual_df['name'] == player['player_name'])
                ]
                
                if not actual_match.empty:
                    players_found += 1
                    actual_total += actual_match.iloc[0]['fanduel_points']
            
            accuracy = (actual_total / projected_total * 100) if projected_total > 0 else 0
            
            lineup_results.append({
                'lineup': lineup_name,
                'projected': projected_total,
                'actual': actual_total,
                'players_found': players_found,
                'total_players': len(lineup_players),
                'accuracy': accuracy
            })
            
            total_projected += projected_total
            total_actual += actual_total
            total_players_found += players_found
            total_players_expected += len(lineup_players)
        
        # Sort by accuracy
        lineup_results.sort(key=lambda x: x['accuracy'], reverse=True)
        
        print("\nLINEUP: LINEUP PERFORMANCE RANKING:")
        print("-" * 80)
        for i, result in enumerate(lineup_results[:5], 1):
            print(f"{i:2d}. {result['lineup']:20} | "
                  f"{result['accuracy']:6.1f}% | "
                  f"{result['actual']:6.1f}/{result['projected']:6.1f} FPPG | "
                  f"{result['players_found']}/{result['total_players']} players")
        
        # Overall statistics
        avg_projected = total_projected / len(unique_lineups)
        avg_actual = total_actual / len(unique_lineups)
        avg_players_found = total_players_found / len(unique_lineups)
        avg_accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
        
        print(f"\nDATA: OVERALL PERFORMANCE:")
        print("-" * 40)
        print(f"Average Projected FPPG: {avg_projected:.1f}")
        print(f"Average Actual FPPG:    {avg_actual:.1f}")
        print(f"Average Players Found:  {avg_players_found:.1f} / 9")
        print(f"Overall Accuracy:       {avg_accuracy:.1f}%")
        print(f"Best Lineup:           {lineup_results[0]['lineup']} ({lineup_results[0]['accuracy']:.1f}%)")
        
        # Performance categorization
        print(f"\nTARGET: PERFORMANCE ASSESSMENT:")
        if avg_accuracy > 80:
            print(" EXCELLENT: System performing at elite level")
        elif avg_accuracy > 60:
            print(" GOOD: System performing well with room for improvement")
        elif avg_accuracy > 40:
            print(" FAIR: System needs significant optimization")
        else:
            print(" POOR: System requires major overhaul")
        
        # Player matching assessment
        match_rate = (total_players_found / total_players_expected) * 100
        print(f" Player Match Rate: {match_rate:.1f}%")
        
        if match_rate < 50:
            print("WARNING:  LOW MATCH RATE: Check player name matching logic")
        elif match_rate < 80:
            print(" MODERATE MATCH RATE: Some players not found in results")
        else:
            print("SUCCESS: GOOD MATCH RATE: Most players successfully matched")
        
        # Save detailed results
        results_df = pd.DataFrame(lineup_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/elite_backtest_results_{timestamp}.csv"
        results_df.to_csv(output_file, index=False)
        print(f"\n Detailed results saved: {os.path.basename(output_file)}")
        
        return lineup_results
        
    except Exception as e:
        print(f"ERROR: Error in backtest analysis: {str(e)}")
        return []

if __name__ == "__main__":
    run_elite_backtest()

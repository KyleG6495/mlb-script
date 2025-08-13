#!/usr/bin/env python3
"""
PRECISE BACKTEST VALIDATOR
Uses strict player matching to avoid false positives
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from precise_player_matcher import PrecisePlayerMatcher

def run_precise_backtest():
    """Run backtest with precise player matching"""
    
    print("🎯 PRECISE BACKTEST VALIDATOR")
    print("=" * 50)
    
    # Load August 9th data
    lineup_file = "../data/final_tournament_lineups_details_20250809_121538.csv"
    results_file = "../data/actual_results_20250809.csv"
    
    print(f"📊 Loading lineups: {os.path.basename(lineup_file)}")
    print(f"📊 Loading results: {os.path.basename(results_file)}")
    
    try:
        # Load data
        lineups_df = pd.read_csv(lineup_file)
        actual_df = pd.read_csv(results_file)
        
        print(f"✅ Loaded {len(lineups_df)} lineup entries")
        print(f"✅ Loaded {len(actual_df)} actual player results")
        
        # Initialize precise matcher
        matcher = PrecisePlayerMatcher()
        
        # Get unique lineups
        unique_lineups = lineups_df['lineup_id'].unique()
        print(f"🏆 Analyzing {len(unique_lineups)} unique lineups")
        
        # Analyze each lineup with precise matching
        lineup_results = []
        total_projected = 0
        total_actual = 0
        total_players_found = 0
        total_players_expected = 0
        
        print(f"\n📊 LINEUP ANALYSIS WITH PRECISE MATCHING:")
        print("-" * 60)
        
        for lineup_name in unique_lineups:
            lineup_players = lineups_df[lineups_df['lineup_id'] == lineup_name]
            
            projected_total = 0
            actual_total = 0
            players_found = 0
            found_players = []
            
            for _, player in lineup_players.iterrows():
                projected_total += player['projected_fppg']
                
                # Use precise matching
                best_match, score = matcher.find_player_match(
                    player['player_name'], actual_df, strict_mode=True
                )
                
                if best_match is not None and score >= 0.95:  # High confidence only
                    players_found += 1
                    actual_fppg = best_match['fanduel_points']
                    actual_total += actual_fppg
                    found_players.append({
                        'name': player['player_name'],
                        'matched': best_match['name'],
                        'projected': player['projected_fppg'],
                        'actual': actual_fppg
                    })
            
            accuracy = (actual_total / projected_total * 100) if projected_total > 0 else 0
            
            lineup_results.append({
                'lineup': lineup_name,
                'projected': projected_total,
                'actual': actual_total,
                'players_found': players_found,
                'total_players': len(lineup_players),
                'accuracy': accuracy,
                'found_players': found_players
            })
            
            total_projected += projected_total
            total_actual += actual_total
            total_players_found += players_found
            total_players_expected += len(lineup_players)
        
        # Sort by number of players found (most useful lineups first)
        lineup_results.sort(key=lambda x: (x['players_found'], x['accuracy']), reverse=True)
        
        print(f"🏆 LINEUP PERFORMANCE (Precise Matching):")
        print("-" * 80)
        
        for i, result in enumerate(lineup_results[:10], 1):
            if result['players_found'] > 0:
                print(f"{i:2d}. {result['lineup']:20} | "
                      f"{result['accuracy']:6.1f}% | "
                      f"{result['actual']:6.1f}/{result['projected']:6.1f} FPPG | "
                      f"{result['players_found']}/{result['total_players']} players")
                
                # Show found players for top lineups
                if i <= 3 and result['found_players']:
                    print(f"    Found players:")
                    for p in result['found_players']:
                        print(f"      {p['name']:20} → {p['matched']:20} "
                              f"({p['projected']:4.1f} → {p['actual']:4.1f})")
                    print()
        
        # Calculate statistics
        lineups_with_players = [r for r in lineup_results if r['players_found'] > 0]
        
        if lineups_with_players:
            avg_projected = np.mean([r['projected'] for r in lineups_with_players])
            avg_actual = np.mean([r['actual'] for r in lineups_with_players])
            avg_players_found = np.mean([r['players_found'] for r in lineups_with_players])
            avg_accuracy = np.mean([r['accuracy'] for r in lineups_with_players])
            
            print(f"\n📊 PRECISE MATCHING STATISTICS:")
            print("-" * 40)
            print(f"Lineups with matched players: {len(lineups_with_players)}/{len(unique_lineups)}")
            print(f"Total players matched: {total_players_found}/{total_players_expected} ({total_players_found/total_players_expected*100:.1f}%)")
            print(f"Average projected FPPG: {avg_projected:.1f}")
            print(f"Average actual FPPG: {avg_actual:.1f}")
            print(f"Average players found: {avg_players_found:.1f}")
            print(f"Average accuracy: {avg_accuracy:.1f}%")
            
            # Find best performing individual players
            all_found_players = []
            for result in lineups_with_players:
                all_found_players.extend(result['found_players'])
            
            if all_found_players:
                # Sort by actual performance
                all_found_players.sort(key=lambda x: x['actual'], reverse=True)
                
                print(f"\n🌟 TOP PERFORMING MATCHED PLAYERS:")
                print("-" * 60)
                for i, player in enumerate(all_found_players[:10], 1):
                    accuracy = (player['actual'] / player['projected'] * 100) if player['projected'] > 0 else 0
                    print(f"{i:2d}. {player['name']:20} | "
                          f"{player['actual']:5.1f} FPPG | "
                          f"{accuracy:5.1f}% accuracy")
        
        else:
            print(f"\n❌ NO LINEUPS WITH MATCHED PLAYERS FOUND")
            print(f"This suggests the lineup data is from a different date than results")
        
        # Save results
        results_df = pd.DataFrame(lineup_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/precise_backtest_results_{timestamp}.csv"
        results_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved: {os.path.basename(output_file)}")
        
        return lineup_results
        
    except Exception as e:
        print(f"❌ Error in precise backtest: {str(e)}")
        return []

if __name__ == "__main__":
    run_precise_backtest()

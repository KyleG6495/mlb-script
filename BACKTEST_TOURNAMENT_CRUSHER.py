import pandas as pd
import numpy as np

def backtest_tournament_lineups():
    """
    Test our new Tournament Crusher lineups against yesterday's actual results
    to see if our improvements would have worked
    """
    
    print("=== TOURNAMENT CRUSHER BACKTEST ===")
    print("Testing our new lineups against yesterday's actual results...")
    print()
    
    # Load our new tournament lineups
    try:
        lineups_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\tournament_crusher_lineups.csv")
        print(f"Loaded {len(lineups_df)} tournament lineups")
    except Exception as e:
        print(f"Error loading lineups: {e}")
        return
    
    # Load yesterday's actual results
    try:
        actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
        print(f"Loaded {len(actual_results)} actual player results")
    except Exception as e:
        print(f"Error loading actual results: {e}")
        return
    
    # Create player name mapping for matching
    actual_results['full_name'] = actual_results['name'].str.strip()
    
    # Score each lineup
    lineup_scores = []
    
    for idx, lineup in lineups_df.iterrows():
        lineup_num = idx + 1
        total_actual_points = 0
        total_salary = 0
        total_projected = 0
        lineup_details = []
        
        # Check each position
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL']
        
        for pos in positions:
            if pos in lineup.index and pd.notna(lineup[pos]):
                player_name = str(lineup[pos]).strip()
                
                # Find this player in actual results
                player_actual = actual_results[actual_results['full_name'] == player_name]
                
                if not player_actual.empty:
                    actual_points = player_actual.iloc[0]['fanduel_points']
                    total_actual_points += actual_points
                    
                    # Try to get salary and projection from the lineup data
                    salary = lineup.get(f'{pos}_salary', 0)
                    projection = lineup.get(f'{pos}_projection', 0)
                    
                    total_salary += salary if pd.notna(salary) else 0
                    total_projected += projection if pd.notna(projection) else 0
                    
                    lineup_details.append({
                        'position': pos,
                        'player': player_name,
                        'actual_points': actual_points,
                        'projected': projection if pd.notna(projection) else 0,
                        'salary': salary if pd.notna(salary) else 0
                    })
                else:
                    # Player not found in yesterday's results (probably didn't play)
                    lineup_details.append({
                        'position': pos,
                        'player': player_name,
                        'actual_points': 0,
                        'projected': lineup.get(f'{pos}_projection', 0),
                        'salary': lineup.get(f'{pos}_salary', 0)
                    })
        
        lineup_scores.append({
            'lineup_num': lineup_num,
            'total_actual': total_actual_points,
            'total_projected': total_projected,
            'total_salary': total_salary,
            'details': lineup_details
        })
    
    # Sort by actual performance
    lineup_scores.sort(key=lambda x: x['total_actual'], reverse=True)
    
    print("\n=== BACKTEST RESULTS ===")
    print("How our Tournament Crusher lineups would have performed yesterday:")
    print()
    
    for i, lineup in enumerate(lineup_scores[:5]):  # Show top 5
        print(f"LINEUP #{lineup['lineup_num']} - ACTUAL: {lineup['total_actual']:.1f} points")
        print(f"Projected: {lineup['total_projected']:.1f} | Salary: ${lineup['total_salary']:,}")
        print("Position | Player | Actual | Projected | Salary")
        print("-" * 55)
        
        for player in lineup['details']:
            print(f"{player['position']:8} | {player['player'][:20]:20} | {player['actual_points']:6.1f} | {player['projected']:9.1f} | ${player['salary']:5}")
        
        print()
    
    # Compare to tournament winner and our original performance
    best_score = max(lineup_scores, key=lambda x: x['total_actual'])['total_actual']
    
    print("=== PERFORMANCE COMPARISON ===")
    print(f"Tournament Winner (yesterday): 306.0 points")
    print(f"Our Original Best (yesterday): 139.9 points")
    print(f"Tournament Crusher Best: {best_score:.1f} points")
    print()
    print(f"Improvement vs Original: +{best_score - 139.9:.1f} points")
    print(f"Gap to Winner: {306.0 - best_score:.1f} points")
    print(f"Performance vs Winner: {best_score/306.0:.1%}")
    
    if best_score > 200:
        print("TARGET: EXCELLENT! Would have been competitive!")
    elif best_score > 180:
        print("SUCCESS: GOOD! Significant improvement over original")
    elif best_score > 160:
        print("PROGRESS: BETTER! Moving in right direction")
    else:
        print("WARNING:  Still needs work, but better than original")
    
    return lineup_scores

if __name__ == "__main__":
    results = backtest_tournament_lineups()

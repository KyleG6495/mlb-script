import pandas as pd
import numpy as np
from itertools import combinations
from pulp import *

def reverse_engineer_yesterday():
    """
    Reverse engineer yesterday's slate to build the perfect optimizer
    Using actual results to see what we should have built
    """
    
    print("=== REVERSE ENGINEERING YESTERDAY'S SLATE ===")
    
    # Load yesterday's actual results
    results_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv"
    results_df = pd.read_csv(results_file)
    
    # Load current slate as proxy for yesterday's pricing (adjust if we find yesterday's)
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    
    try:
        slate_df = pd.read_csv(slate_file)
    except:
        slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_today.csv"
        slate_df = pd.read_csv(slate_file)
    
    print(f"Loaded {len(results_df)} actual results")
    print(f"Loaded {len(slate_df)} slate players")
    
    # Merge results with slate data (match by name for now)
    print("\n=== MERGING ACTUAL RESULTS WITH SLATE DATA ===")
    
    # Create a merged dataset
    merged_data = []
    
    for _, result_row in results_df.iterrows():
        result_name = result_row['name']
        result_pos = result_row['position']
        actual_points = result_row['fanduel_points']
        
        # Try to find matching player in slate
        slate_matches = slate_df[
            (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.contains(result_name.split()[0], case=False, na=False) |
            (slate_df['Nickname'].str.contains(result_name.split()[0], case=False, na=False))
        ]
        
        if not slate_matches.empty:
            best_match = slate_matches.iloc[0]
            merged_data.append({
                'name': result_name,
                'id': best_match['Id'],
                'position': best_match['Position'],
                'salary': best_match['Salary'],
                'projected_fppg': best_match['FPPG'],
                'actual_fppg': actual_points,
                'value': actual_points / best_match['Salary'] * 1000,  # Points per $1K
                'projection_error': actual_points - best_match['FPPG']
            })
    
    merged_df = pd.DataFrame(merged_data)
    
    if merged_df.empty:
        print("ERROR: Could not merge data - likely different date ranges")
        return
    
    print(f"Successfully merged {len(merged_df)} players")
    
    # Analyze the biggest misses
    print("\n=== BIGGEST PROJECTION ERRORS ===")
    biggest_misses = merged_df.nlargest(10, 'projection_error')
    print(biggest_misses[['name', 'position', 'salary', 'projected_fppg', 'actual_fppg', 'projection_error']].to_string(index=False))
    
    # Find the optimal lineup using ACTUAL results
    print("\n=== BUILDING OPTIMAL LINEUP WITH ACTUAL RESULTS ===")
    
    # Filter players by position for optimal lineup building
    pitchers = merged_df[merged_df['position'].str.contains('P', case=False, na=False)]
    catchers = merged_df[merged_df['position'].str.contains('C', case=False, na=False)]
    first_base = merged_df[merged_df['position'].str.contains('1B', case=False, na=False)]
    second_base = merged_df[merged_df['position'].str.contains('2B', case=False, na=False)]
    third_base = merged_df[merged_df['position'].str.contains('3B', case=False, na=False)]
    shortstop = merged_df[merged_df['position'].str.contains('SS', case=False, na=False)]
    outfield = merged_df[merged_df['position'].str.contains('OF', case=False, na=False)]
    
    print(f"Position breakdown:")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Catchers: {len(catchers)}")
    print(f"1B: {len(first_base)}")
    print(f"2B: {len(second_base)}")
    print(f"3B: {len(third_base)}")
    print(f"SS: {len(shortstop)}")
    print(f"OF: {len(outfield)}")
    
    # Build the theoretically perfect lineup
    if len(pitchers) > 0 and len(outfield) >= 3:
        best_pitcher = pitchers.nlargest(1, 'actual_fppg').iloc[0]
        best_of = outfield.nlargest(3, 'actual_fppg')
        
        # Build a simple optimal lineup
        optimal_lineup = []
        total_salary = 0
        total_points = 0
        
        # Add best pitcher
        optimal_lineup.append(('P', best_pitcher))
        total_salary += best_pitcher['salary']
        total_points += best_pitcher['actual_fppg']
        
        # Add best 3 OF
        for i, (_, of_player) in enumerate(best_of.iterrows()):
            optimal_lineup.append((f'OF{i+1}', of_player))
            total_salary += of_player['salary']
            total_points += of_player['actual_fppg']
        
        # Add best from other positions (if available)
        for pos_name, pos_df in [('C/1B', catchers), ('2B', second_base), ('3B', third_base), ('SS', shortstop)]:
            if not pos_df.empty and total_salary < 45000:  # Leave room for UTIL
                best_pos = pos_df.nlargest(1, 'actual_fppg').iloc[0]
                if total_salary + best_pos['salary'] <= 48000:  # Conservative salary cap
                    optimal_lineup.append((pos_name, best_pos))
                    total_salary += best_pos['salary']
                    total_points += best_pos['actual_fppg']
        
        # Add UTIL (best remaining value)
        remaining_players = merged_df[~merged_df['name'].isin([player['name'] for _, player in optimal_lineup])]
        if not remaining_players.empty and total_salary < 48000:
            remaining_budget = 50000 - total_salary
            affordable_util = remaining_players[remaining_players['salary'] <= remaining_budget]
            if not affordable_util.empty:
                best_util = affordable_util.nlargest(1, 'actual_fppg').iloc[0]
                optimal_lineup.append(('UTIL', best_util))
                total_salary += best_util['salary']
                total_points += best_util['actual_fppg']
        
        print(f"\n=== THEORETICAL OPTIMAL LINEUP ===")
        print(f"Total Salary: ${total_salary:,}")
        print(f"Total Points: {total_points:.1f}")
        print(f"Remaining Salary: ${50000 - total_salary:,}")
        
        for pos, player in optimal_lineup:
            print(f"{pos}: {player['name']} (${player['salary']}, {player['actual_fppg']:.1f} pts)")
        
        # Compare to winning score of 306
        print(f"\nWinning score was: 306.0")
        print(f"Our optimal would be: {total_points:.1f}")
        print(f"Difference: {306.0 - total_points:.1f}")
        
        if total_points >= 300:
            print("TARGET: WE COULD HAVE WON!")
        elif total_points >= 270:
            print(" We could have placed top 3!")
        else:
            print(" Still need better player selection strategy")
    
    # Save the analysis
    analysis_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\reverse_engineering_analysis.csv"
    merged_df.to_csv(analysis_file, index=False)
    print(f"\nAnalysis saved to: {analysis_file}")
    
    return merged_df

if __name__ == "__main__":
    reverse_engineer_yesterday()

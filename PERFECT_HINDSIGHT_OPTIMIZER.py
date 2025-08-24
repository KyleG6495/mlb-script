import pandas as pd
import numpy as np
from itertools import combinations

def build_perfect_hindsight_optimizer():
    """
    Reverse-engineer yesterday's slate with actual results to build the 
    perfect optimizer that would have found the winning 306-point lineup
    """
    
    print("=== PERFECT HINDSIGHT OPTIMIZER ===")
    print("Building the optimal lineup using yesterday's actual results...")
    print()
    
    # Load actual results from yesterday
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    print("Top 20 actual performers:")
    top_performers = actual_results.nlargest(20, 'fanduel_points')
    print(top_performers[['name', 'position', 'team', 'fanduel_points']].to_string(index=False))
    print()
    
    # Try to load yesterday's slate data
    try:
        # Check if we have a saved slate from yesterday
        slate_files = [
            r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv",
            r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_today.csv"
        ]
        
        slate_df = None
        for file in slate_files:
            try:
                slate_df = pd.read_csv(file)
                print(f"Loaded slate data from: {file}")
                break
            except:
                continue
        
        if slate_df is None:
            print("ERROR: Could not find yesterday's slate data")
            print("We need the original FanDuel slate with salaries and positions")
            return
        
        # Match actual results with slate data
        # Create a mapping by player name
        actual_results['full_name'] = actual_results['name'].str.strip()
        slate_df['full_name'] = (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.strip()
        
        # Merge actual results with slate data
        merged_data = slate_df.merge(
            actual_results[['full_name', 'fanduel_points']], 
            on='full_name', 
            how='left'
        )
        
        # Fill missing scores with 0 (players who didn't play or scored 0)
        merged_data['actual_fppg'] = merged_data['fanduel_points'].fillna(0)
        
        print(f"\nMatched {len(merged_data[merged_data['actual_fppg'] > 0])} players with actual scores")
        
        # Show the biggest differences between projected and actual
        merged_data['projection_error'] = merged_data['actual_fppg'] - merged_data['FPPG']
        
        print("\nBiggest POSITIVE surprises (actual >> projected):")
        surprises = merged_data[merged_data['projection_error'] > 10].sort_values('projection_error', ascending=False)
        print(surprises[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'actual_fppg', 'projection_error']].head(10).to_string(index=False))
        
        print("\nBiggest NEGATIVE surprises (projected >> actual):")
        busts = merged_data[merged_data['projection_error'] < -10].sort_values('projection_error')
        print(busts[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'actual_fppg', 'projection_error']].head(10).to_string(index=False))
        
        # Now build the PERFECT lineup using actual scores
        print("\n=== BUILDING PERFECT LINEUP ===")
        
        # Filter to players who actually played (had stats)
        available_players = merged_data[merged_data['actual_fppg'] >= 0].copy()
        
        # Position mappings for FanDuel
        position_mapping = {
            'P': ['P'],
            'C/1B': ['C', 'C/1B', '1B'],
            '2B': ['2B'],
            '3B': ['3B'],
            'SS': ['SS'],
            'OF': ['OF'],
            'UTIL': ['C', 'C/1B', '1B', '2B', '3B', 'SS', 'OF', 'DH']
        }
        
        def can_play_position(player_pos, needed_pos):
            """Check if player can play the needed position"""
            if needed_pos == 'UTIL':
                return any(pos in player_pos for pos in position_mapping['UTIL'])
            else:
                return any(pos in player_pos for pos in position_mapping[needed_pos])
        
        # Build optimal lineup
        lineup_positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        # Greedy approach: pick best available player for each position
        selected_players = []
        used_players = set()
        total_salary = 0
        total_points = 0
        
        for pos in lineup_positions:
            # Find best available player for this position
            eligible = available_players[
                (available_players['Position'].apply(lambda x: can_play_position(x, pos))) &
                (~available_players.index.isin(used_players))
            ].sort_values('actual_fppg', ascending=False)
            
            if len(eligible) > 0:
                best_player = eligible.iloc[0]
                selected_players.append({
                    'position': pos,
                    'name': f"{best_player['First Name']} {best_player['Last Name']}",
                    'salary': best_player['Salary'],
                    'projected': best_player['FPPG'],
                    'actual': best_player['actual_fppg'],
                    'team': best_player.get('Team', 'N/A')
                })
                used_players.add(best_player.name)
                total_salary += best_player['Salary']
                total_points += best_player['actual_fppg']
        
        print("\nPERFECT HINDSIGHT LINEUP:")
        print("Position | Player | Team | Salary | Projected | ACTUAL")
        print("-" * 60)
        for player in selected_players:
            print(f"{player['position']:8} | {player['name']:20} | {player['team']:4} | ${player['salary']:5} | {player['projected']:8.1f} | {player['actual']:6.1f}")
        
        print(f"\nTotal Salary: ${total_salary:,}")
        print(f"Salary Remaining: ${50000 - total_salary:,}")
        print(f"Total Actual Points: {total_points:.1f}")
        print(f"Tournament Winner: 306.0")
        print(f"Our Performance Gap: {306.0 - total_points:.1f} points")
        
        # Analyze what went wrong with our original strategy
        print("\n=== LESSONS LEARNED ===")
        
        lessons = []
        
        if total_salary < 47000:
            lessons.append("1. SALARY USAGE: We need to spend more money on studs")
        
        if total_points < 280:
            lessons.append("2. CEILING FOCUS: Target high-upside plays over safe floors")
        
        # Check if we missed obvious studs
        top_studs = merged_data.nlargest(5, 'actual_fppg')
        our_picks = [p['name'] for p in selected_players]
        missed_studs = []
        
        for _, stud in top_studs.iterrows():
            stud_name = f"{stud['First Name']} {stud['Last Name']}"
            if stud_name not in our_picks:
                missed_studs.append(f"{stud_name} ({stud['actual_fppg']:.1f} pts)")
        
        if missed_studs:
            lessons.append(f"3. MISSED STUDS: {', '.join(missed_studs[:3])}")
        
        lessons.append("4. CORRELATION: Stack hitters from high-scoring games")
        lessons.append("5. CONTRARIAN PLAYS: Target lower-owned players with upside")
        
        for lesson in lessons:
            print(lesson)
        
        return merged_data, selected_players
    
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    merged_data, perfect_lineup = build_perfect_hindsight_optimizer()

import pandas as pd
import numpy as np
import pulp

def test_tournament_crusher_on_august_12():
    """
    Apply our Tournament Crusher strategy to August 12th's actual slate
    and see if it would have found the 306-point winning lineup
    """
    
    print("=== TOURNAMENT CRUSHER: AUGUST 12TH SLATE TEST ===")
    print("Testing our new strategy on yesterday's actual slate...")
    print()
    
    # Load August 12th slate data
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv"
    slate_df = pd.read_csv(slate_file)
    
    # Load actual results from August 12th
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    print(f"Loaded {len(slate_df)} players from August 12th slate")
    print(f"Loaded {len(actual_results)} actual results")
    
    # Merge slate with actual results
    actual_results['full_name'] = actual_results['name'].str.strip()
    slate_df['full_name'] = (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.strip()
    
    merged_data = slate_df.merge(
        actual_results[['full_name', 'fanduel_points']], 
        on='full_name', 
        how='left'
    )
    
    # Fill missing scores with 0
    merged_data['actual_fppg'] = merged_data['fanduel_points'].fillna(0)
    
    print(f"Matched {len(merged_data[merged_data['actual_fppg'] > 0])} players with actual scores")
    
    # Apply Tournament Crusher adjustments to August 12th slate
    merged_data['tournament_projection'] = merged_data['FPPG'].fillna(0).copy()
    
    # Handle any remaining NaN values
    merged_data = merged_data.fillna(0)
    
    # Boost cheap high-upside players (salary <= $3000, FPPG >= 8)
    cheap_upside = (merged_data['Salary'] <= 3000) & (merged_data['FPPG'] >= 8)
    merged_data.loc[cheap_upside, 'tournament_projection'] *= 1.3
    
    # Boost mid-tier ceiling players ($3000-$4000, FPPG >= 10)
    mid_ceiling = (merged_data['Salary'] >= 3000) & (merged_data['Salary'] <= 4000) & (merged_data['FPPG'] >= 10)
    merged_data.loc[mid_ceiling, 'tournament_projection'] *= 1.2
    
    # Penalize expensive pitchers who might bust (salary >= $10500)
    expensive_pitchers = (merged_data['Position'] == 'P') & (merged_data['Salary'] >= 10500)
    merged_data.loc[expensive_pitchers, 'tournament_projection'] *= 0.9
    
    # Boost mid-tier pitchers ($8000-$10000)
    mid_pitchers = (merged_data['Position'] == 'P') & (merged_data['Salary'] >= 8000) & (merged_data['Salary'] <= 10000)
    merged_data.loc[mid_pitchers, 'tournament_projection'] *= 1.15
    
    print("\nApplied Tournament Crusher adjustments:")
    print(f"- Boosted {cheap_upside.sum()} cheap upside players")
    print(f"- Boosted {mid_ceiling.sum()} mid-tier ceiling players") 
    print(f"- Penalized {expensive_pitchers.sum()} expensive pitchers")
    print(f"- Boosted {mid_pitchers.sum()} mid-tier pitchers")
    
    # Show top value plays
    merged_data['value_score'] = merged_data['tournament_projection'] / (merged_data['Salary'] / 1000)
    
    print("\nTop 10 VALUE plays after adjustments:")
    top_value = merged_data.nlargest(10, 'value_score')
    print(top_value[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'tournament_projection', 'actual_fppg', 'value_score']].to_string(index=False))
    
    print("\nTop 10 ACTUAL performers (what we should have found):")
    top_actual = merged_data.nlargest(10, 'actual_fppg')
    print(top_actual[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'tournament_projection', 'actual_fppg', 'value_score']].to_string(index=False))
    
    # Now optimize lineup using our Tournament Crusher approach
    print("\n=== OPTIMIZING LINEUP ===")
    
    # Filter available players
    available_players = merged_data[merged_data['Salary'] > 0].copy().reset_index(drop=True)
    
    # Set up optimization
    prob = pulp.LpProblem("Tournament_Crusher_Aug12", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize tournament projection
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'tournament_projection'] for i in range(len(available_players))])
    
    # Salary constraints
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) <= 35000
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) >= 34000
    
    # Position constraints
    def can_play_position(player_pos, needed_pos):
        if needed_pos == 'UTIL':
            return any(pos in str(player_pos) for pos in ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH'])
        elif needed_pos == 'C/1B':
            return any(pos in str(player_pos) for pos in ['C', '1B'])
        else:
            return needed_pos in str(player_pos)
    
    # Position requirements
    positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
    
    for pos in positions_needed:
        eligible_indices = [i for i in range(len(available_players)) 
                          if can_play_position(available_players.loc[i, 'Position'], pos)]
        if eligible_indices:
            prob += pulp.lpSum([player_vars[i] for i in eligible_indices]) >= 1
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:  # Optimal
        selected_players = []
        total_salary = 0
        total_projected = 0
        total_actual = 0
        
        for i in range(len(available_players)):
            if player_vars[i].value() == 1:
                player = available_players.loc[i]
                selected_players.append(player)
                total_salary += player['Salary']
                total_projected += player['tournament_projection']
                total_actual += player['actual_fppg']
        
        print("\n=== TOURNAMENT CRUSHER LINEUP (August 12th) ===")
        print("Player | Position | Salary | Projected | ACTUAL | Value")
        print("-" * 70)
        
        for player in selected_players:
            print(f"{player['First Name']} {player['Last Name']:15} | {player['Position']:8} | ${player['Salary']:5} | {player['tournament_projection']:8.1f} | {player['actual_fppg']:6.1f} | {player['value_score']:5.1f}")
        
        print(f"\nTotal Salary: ${total_salary:,}")
        print(f"Salary Usage: {total_salary/35000:.1%}")
        print(f"Tournament Projection: {total_projected:.1f}")
        print(f"ACTUAL PERFORMANCE: {total_actual:.1f}")
        
        print("\n=== COMPARISON ===")
        print(f"Tournament Winner: 306.0 points")
        print(f"Our Original Best: 139.9 points") 
        print(f"Tournament Crusher: {total_actual:.1f} points")
        print(f"Improvement: +{total_actual - 139.9:.1f} points")
        print(f"Gap to Winner: {306.0 - total_actual:.1f} points")
        
        if total_actual > 250:
            print("🏆 CHAMPION LEVEL! Would have won or placed high!")
        elif total_actual > 200:
            print("🎯 EXCELLENT! Would have been very competitive!")
        elif total_actual > 160:
            print("✅ GOOD! Significant improvement!")
        else:
            print("📈 BETTER! Still room for improvement")
            
        return selected_players, total_actual
    
    else:
        print("Optimization failed!")
        return None, 0

if __name__ == "__main__":
    lineup, score = test_tournament_crusher_on_august_12()

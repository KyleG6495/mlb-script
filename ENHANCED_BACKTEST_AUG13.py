#!/usr/bin/env python3
"""
ENHANCED BACKTEST - Check if winners were in our August 13th data
"""

import pandas as pd
import numpy as np

def check_winners_in_projections():
    """Check if August 13th winners were in our projection data"""
    
    print(" ENHANCED BACKTEST: WINNERS IN PROJECTIONS CHECK")
    print("=" * 60)
    
    try:
        # Load August 13th projections
        df_projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        print(f"SUCCESS: Loaded projections: {len(df_projections)} players")
        
        # Load actual results
        df_results = pd.read_csv("../data/actual_results_latest.csv")
        print(f"SUCCESS: Loaded actual results: {len(df_results)} players")
        
        # Known winners from actual results
        winner_ids = [805300, 669364, 671739, 683746]  # Jakob, Xavier, Harris, Ozuna
        winner_names = ['Jakob Marsee', 'Xavier Edwards', 'Michael Harris II', 'Marcell Ozuna']
        
        print(f"\nLINEUP: CHECKING FOR AUGUST 13TH WINNERS IN PROJECTIONS:")
        print("=" * 55)
        
        for i, player_id in enumerate(winner_ids):
            # Get actual performance
            actual_row = df_results[df_results['player_id'] == player_id]
            if len(actual_row) > 0:
                actual_points = actual_row.iloc[0]['fanduel_points']
                player_name = actual_row.iloc[0]['name']
                team = actual_row.iloc[0]['team']
                
                print(f"\n Searching for {player_name} ({team}) - {actual_points} actual pts")
                
                # Search in projections by player_id
                proj_row = df_projections[df_projections['player_id'] == player_id]
                if len(proj_row) > 0:
                    player_proj = proj_row.iloc[0]
                    salary = player_proj['Salary']
                    base_proj = player_proj['FPPG']
                    enhanced_proj = player_proj['enhanced_fppg']
                    
                    print(f"  SUCCESS: FOUND IN PROJECTIONS!")
                    print(f"     Salary: ${salary}")
                    print(f"     Base Projection: {base_proj:.1f} pts")
                    print(f"     Enhanced Projection: {enhanced_proj:.1f} pts")
                    print(f"     Actual Performance: {actual_points:.1f} pts")
                    print(f"     Projection Accuracy: {(enhanced_proj/actual_points*100):.1f}%")
                    
                    # Calculate what aggressive system would have projected
                    upside_multiplier = calculate_aggressive_multiplier(player_proj)
                    aggressive_proj = enhanced_proj * upside_multiplier
                    
                    print(f"     START: AGGRESSIVE PROJECTION: {aggressive_proj:.1f} pts (x{upside_multiplier:.2f})")
                    print(f"     TARGET: Aggressive Accuracy: {(aggressive_proj/actual_points*100):.1f}%")
                    
                    if aggressive_proj >= 25:
                        print(f"      WOULD HAVE BEEN NUCLEAR VALUE TARGET!")
                else:
                    print(f"  ERROR: NOT FOUND in projections data")
        
        # Now run full aggressive analysis
        run_full_aggressive_analysis(df_projections, df_results)
        
    except Exception as e:
        print(f"ERROR: Error: {e}")

def calculate_aggressive_multiplier(player):
    """Calculate aggressive multiplier for a player"""
    
    base_multiplier = 1.0
    salary = player['Salary']
    
    # Salary-based upside
    if salary <= 2500:
        base_multiplier += 0.6
    elif salary <= 3000:
        base_multiplier += 0.4
    elif salary <= 3500:
        base_multiplier += 0.2
    
    # Position-based adjustments
    if player['Position'] in ['OF', 'SS', '2B']:
        base_multiplier += 0.1
    
    # Batting order boost
    batting_order = player.get('Batting Order', 5)
    if batting_order <= 3:
        base_multiplier += 0.15
    elif batting_order <= 5:
        base_multiplier += 0.1
    
    return min(base_multiplier, 2.0)

def run_full_aggressive_analysis(df_projections, df_results):
    """Run full aggressive system analysis"""
    
    print(f"\nSTART: FULL AGGRESSIVE SYSTEM ANALYSIS")
    print("=" * 40)
    
    # Merge projections with results
    df_merged = df_projections.merge(
        df_results[['player_id', 'fanduel_points']], 
        on='player_id', 
        how='left'
    )
    df_merged['actual_points'] = df_merged['fanduel_points'].fillna(0)
    
    # Apply aggressive system
    df_merged['base_projection'] = df_merged['enhanced_fppg']
    df_merged['aggressive_projection'] = df_merged['base_projection'].copy()
    
    # Find value players and apply boosts
    value_players = df_merged[
        (df_merged['Salary'] <= 3500) & 
        (df_merged['Position'] != 'P') &
        (df_merged['Batting Order'] > 0)  # Starting players only
    ].copy()
    
    nuclear_targets = []
    
    for idx, player in value_players.iterrows():
        original_proj = player['base_projection']
        upside_multiplier = calculate_aggressive_multiplier(player)
        enhanced_proj = original_proj * upside_multiplier
        
        df_merged.at[idx, 'aggressive_projection'] = enhanced_proj
        
        if enhanced_proj >= 25:  # Nuclear threshold
            nuclear_targets.append({
                'name': f"{player['Nickname']} {player['Last Name']}",
                'team': player['Team'],
                'salary': player['Salary'],
                'original_proj': original_proj,
                'aggressive_proj': enhanced_proj,
                'actual_points': player['actual_points'],
                'multiplier': upside_multiplier,
                'pts_per_k': enhanced_proj / (player['Salary'] / 1000)
            })
    
    # Sort nuclear targets by aggressive projection
    nuclear_targets.sort(key=lambda x: x['aggressive_proj'], reverse=True)
    
    print(f"\nTARGET: NUCLEAR VALUE TARGETS (25 pts projected):")
    print("-" * 50)
    
    total_found = 0
    total_actual = 0
    
    for target in nuclear_targets:
        print(f" {target['name']} ({target['team']}) - ${target['salary']}")
        print(f"   Aggressive Proj: {target['aggressive_proj']:.1f} pts ({target['pts_per_k']:.1f} pts/$K)")
        print(f"   Actual Result: {target['actual_points']:.1f} pts")
        
        if target['actual_points'] >= 25:
            print(f"   SUCCESS: SUCCESS! Actually scored {target['actual_points']:.1f} pts")
            total_found += 1
        else:
            print(f"   ERROR: Missed - only {target['actual_points']:.1f} pts")
        
        total_actual += target['actual_points']
        print()
    
    if len(nuclear_targets) > 0:
        avg_actual = total_actual / len(nuclear_targets)
        success_rate = (total_found / len(nuclear_targets)) * 100
        
        print(f"DATA: NUCLEAR TARGET SUMMARY:")
        print(f"   Total Targets: {len(nuclear_targets)}")
        print(f"   Successful (25 pts): {total_found} ({success_rate:.1f}%)")
        print(f"   Average Actual Score: {avg_actual:.1f} pts")
    
    # Build sample lineup
    build_sample_aggressive_lineup(df_merged)

def build_sample_aggressive_lineup(df):
    """Build a sample aggressive lineup for August 13th"""
    
    print(f"\n SAMPLE AGGRESSIVE LINEUP FOR AUGUST 13TH")
    print("=" * 45)
    
    # Filter to starting players
    probable_pitchers = df[
        (df['Position'] == 'P') & 
        (df['Probable Pitcher'] == 'Yes')
    ].copy()
    
    starting_hitters = df[
        (df['Position'] != 'P') & 
        (df['Batting Order'] > 0)
    ].copy()
    
    # Get value pitcher
    value_pitchers = probable_pitchers[
        (probable_pitchers['Salary'] >= 6000) & 
        (probable_pitchers['Salary'] <= 10000)
    ].sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        print("ERROR: No value pitchers found")
        return
    
    # Build lineup
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with best value pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['player_id'])
    
    # Fill positions
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_for_position_backtest(pos, starting_hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['player_id'])
    
    # Display lineup
    if len(lineup) == 9:
        display_backtest_lineup(lineup)
    else:
        print(f"ERROR: Could only build {len(lineup)}/9 positions")

def find_best_for_position_backtest(position, players, max_salary, used_players):
    """Find best available player for position"""
    
    if position == 'C':
        eligible = players[players['Position'].str.contains('C')]
    elif position in ['1B', '2B', '3B', 'SS']:
        eligible = players[players['Position'].str.contains(position)]
    elif position == 'OF':
        eligible = players[players['Position'].str.contains('OF')]
    else:
        eligible = players
    
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['player_id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    return available.nlargest(1, 'aggressive_projection').iloc[0]

def display_backtest_lineup(lineup):
    """Display the backtest lineup with actual results"""
    
    print(f"\nINFO: AGGRESSIVE SYSTEM LINEUP:")
    print("-" * 35)
    
    total_salary = 0
    total_projected = 0
    total_actual = 0
    
    for pos, player in lineup:
        salary = player['Salary']
        projected = player['aggressive_projection']
        actual = player['actual_points']
        
        total_salary += salary
        total_projected += projected
        total_actual += actual
        
        print(f"{pos:4}: {player['Nickname']} {player['Last Name']} ({player['Team']})")
        print(f"      ${salary} - Proj: {projected:.1f}, Actual: {actual:.1f}")
    
    print(f"\nMONEY: LINEUP TOTALS:")
    print(f"   Salary: ${total_salary:,} (${35000-total_salary:,} remaining)")
    print(f"   Projected: {total_projected:.1f} pts")
    print(f"   Actual: {total_actual:.1f} pts")
    print(f"   Accuracy: {(total_projected/total_actual*100):.1f}%" if total_actual > 0 else "N/A")
    
    # Compare to winning score
    winning_score = 271.6
    print(f"\nLINEUP: vs WINNING SCORE: {winning_score} pts")
    print(f"   Gap: {winning_score - total_actual:.1f} pts")
    if total_actual >= winning_score:
        print(f"   COMPLETE: WOULD HAVE WON!")
    elif total_actual >= 200:
        print(f"   MONEY: Would have cashed!")
    else:
        print(f"   ERROR: Would not have cashed")

if __name__ == "__main__":
    check_winners_in_projections()

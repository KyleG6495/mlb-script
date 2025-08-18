#!/usr/bin/env python3
"""
proper_backtest_analysis.py
Backtest yesterday's slate against actual August 7th results
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re

def main():
    """Run proper backtest analysis"""
    
    print("PROPER BACKTEST ANALYSIS")
    print("=" * 50)
    print("Comparing yesterday's slate vs August 7th actual results")
    print()
    
    # Step 1: Load yesterday's slate
    print("1. Loading yesterday's slate...")
    slate_df = load_yesterdays_slate()
    
    # Step 2: Load actual results from August 7th
    print("2. Loading August 7th actual results...")
    results_df = load_actual_results()
    
    # Step 3: Match players and analyze
    print("3. Matching players and analyzing performance...")
    analysis = analyze_performance(slate_df, results_df)
    
    # Step 4: Backtest our conservative lineups
    print("4. Backtesting conservative lineup approach...")
    lineup_performance = backtest_conservative_approach(slate_df, results_df)
    
    # Step 5: Show comprehensive results
    print("5. Comprehensive backtest results...")
    show_backtest_results(analysis, lineup_performance)

def load_yesterdays_slate():
    """Load yesterday's slate data"""
    
    slate_file = "../data/fd_slate_starters_only.csv"
    df = pd.read_csv(slate_file)
    
    print(f"   Loaded {len(df)} players from yesterday's slate")
    
    # Clean player names for matching
    df['clean_name'] = df['First Name'].str.strip() + ' ' + df['Last Name'].str.strip()
    df['clean_name'] = df['clean_name'].str.upper()
    
    return df

def load_actual_results():
    """Load actual results from August 7th"""
    
    results_file = "../data/actual_results_20250807.csv"
    df = pd.read_csv(results_file)
    
    print(f"   Loaded {len(df)} actual results from August 7th")
    
    # Clean names for matching
    df['clean_name'] = df['name'].str.strip().str.upper()
    
    return df

def analyze_performance(slate_df, results_df):
    """Analyze player performance - slate vs actual"""
    
    # Merge slate with actual results
    merged = slate_df.merge(
        results_df[['clean_name', 'fanduel_points', 'team', 'position']], 
        on='clean_name', 
        how='left',
        suffixes=('_slate', '_actual')
    )
    
    # Calculate matching stats
    total_slate_players = len(slate_df)
    matched_players = merged['fanduel_points'].notna().sum()
    match_rate = (matched_players / total_slate_players) * 100
    
    print(f"   Player matching: {matched_players}/{total_slate_players} ({match_rate:.1f}%)")
    
    # For matched players, compare projections vs actual
    matched_only = merged[merged['fanduel_points'].notna()].copy()
    
    if len(matched_only) > 0:
        # Use conservative projections we created
        matched_only['conservative_fppg'] = get_conservative_projection(matched_only)
        
        avg_actual = matched_only['fanduel_points'].mean()
        avg_projected = matched_only['conservative_fppg'].mean()
        
        print(f"   Average actual FPPG: {avg_actual:.1f}")
        print(f"   Average conservative projection: {avg_projected:.1f}")
        print(f"   Projection accuracy: {(1 - abs(avg_actual - avg_projected) / avg_actual) * 100:.1f}%")
        
        return {
            'total_players': total_slate_players,
            'matched_players': matched_players,
            'match_rate': match_rate,
            'avg_actual': avg_actual,
            'avg_projected': avg_projected,
            'matched_data': matched_only
        }
    else:
        print("   No players matched for detailed analysis")
        return {
            'total_players': total_slate_players,
            'matched_players': 0,
            'match_rate': 0,
            'avg_actual': 0,
            'avg_projected': 0,
            'matched_data': pd.DataFrame()
        }

def get_conservative_projection_single(player):
    """Get conservative projection for a single player"""
    
    pos = str(player.get('Position', '')).upper()
    
    # Conservative estimates based on position
    if 'P' in pos:
        return 25.0  # Conservative pitcher projection
    elif any(x in pos for x in ['C']):
        return 8.0   # Conservative catcher projection
    elif any(x in pos for x in ['1B', '2B', '3B', 'SS']):
        return 9.0   # Conservative infield projection
    elif any(x in pos for x in ['OF', 'LF', 'CF', 'RF']):
        return 8.5   # Conservative outfield projection
    else:
        return 8.0   # Default conservative projection

def get_conservative_projection(df):
    """Get conservative projections based on position"""
    
    projections = []
    
    for _, player in df.iterrows():
        projections.append(get_conservative_projection_single(player))
    
    return projections

def backtest_conservative_approach(slate_df, results_df):
    """Backtest our conservative lineup building approach"""
    
    print("   Simulating conservative lineup construction...")
    
    # Simulate building a conservative lineup using yesterday's slate
    lineup_players = build_conservative_lineup_simulation(slate_df)
    
    if not lineup_players:
        print("   Could not simulate lineup construction")
        return None
    
    # Check how this lineup would have performed
    lineup_performance = calculate_lineup_performance(lineup_players, results_df)
    
    return lineup_performance

def build_conservative_lineup_simulation(slate_df):
    """Simulate building a conservative lineup from yesterday's slate"""
    
    # Simplify positions
    slate_df = slate_df.copy()
    slate_df['Simple_Position'] = slate_df['Position'].apply(simplify_position)
    
    # Add conservative projections
    slate_df['Conservative_FPPG'] = get_conservative_projection(slate_df)
    
    try:
        selected_players = []
        total_salary = 0
        salary_cap = 35000
        
        # Select one player per position using conservative approach
        positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        
        for pos in positions:
            pos_players = slate_df[slate_df['Simple_Position'] == pos]
            
            if len(pos_players) == 0:
                continue
            
            # Filter by salary budget
            remaining_salary = salary_cap - total_salary
            remaining_positions = len(positions) - len(selected_players)
            
            if remaining_positions > 0:
                budget_per_position = remaining_salary / remaining_positions
                affordable = pos_players[pos_players['Salary'] <= budget_per_position * 1.5]
            else:
                affordable = pos_players
            
            if len(affordable) == 0:
                affordable = pos_players.nsmallest(3, 'Salary')
            
            # Select best value player
            affordable = affordable.copy()
            affordable['value_score'] = affordable['Conservative_FPPG'] / (affordable['Salary'] / 1000)
            
            selected = affordable.nlargest(1, 'value_score').iloc[0]
            selected_players.append(selected)
            total_salary += selected['Salary']
        
        if len(selected_players) == 9 and total_salary <= salary_cap:
            print(f"   Simulated lineup: 9 players, ${total_salary:,} salary")
            return selected_players
        else:
            print(f"   Simulation failed: {len(selected_players)} players, ${total_salary:,}")
            return None
            
    except Exception as e:
        print(f"   Simulation error: {e}")
        return None

def simplify_position(pos):
    """Simplify position for lineup building"""
    if pd.isna(pos):
        return 'UTIL'
    
    pos = str(pos).upper()
    if 'P' in pos: return 'P'
    if pos.startswith('C'): return 'C'
    if '1B' in pos: return '1B'
    if '2B' in pos: return '2B'
    if '3B' in pos: return '3B'
    if 'SS' in pos: return 'SS'
    if any(x in pos for x in ['OF', 'LF', 'CF', 'RF']): return 'OF'
    return 'UTIL'

def calculate_lineup_performance(lineup_players, results_df):
    """Calculate how the simulated lineup would have performed"""
    
    total_projected = 0
    total_actual = 0
    players_found = 0
    
    lineup_details = []
    
    for player in lineup_players:
        player_name = f"{player['First Name']} {player['Last Name']}".strip().upper()
        projected = get_conservative_projection_single(player)
        
        # Find actual performance
        actual_result = results_df[results_df['clean_name'] == player_name]
        
        if len(actual_result) > 0:
            actual_fppg = actual_result.iloc[0]['fanduel_points']
            players_found += 1
        else:
            actual_fppg = 0
        
        total_projected += projected
        total_actual += actual_fppg
        
        lineup_details.append({
            'player_name': player_name,
            'position': player['Position'],
            'salary': player['Salary'],
            'projected_fppg': projected,
            'actual_fppg': actual_fppg,
            'found': len(actual_result) > 0
        })
    
    accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
    
    return {
        'total_projected': total_projected,
        'total_actual': total_actual,
        'players_found': players_found,
        'total_players': len(lineup_players),
        'accuracy_pct': accuracy,
        'lineup_details': lineup_details
    }

def show_backtest_results(analysis, lineup_performance):
    """Show comprehensive backtest results"""
    
    print()
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 50)
    
    # Player matching results
    print(f"PLAYER MATCHING:")
    print(f"  Total slate players: {analysis['total_players']}")
    print(f"  Players found in results: {analysis['matched_players']}")
    print(f"  Match rate: {analysis['match_rate']:.1f}%")
    
    if analysis['matched_players'] > 0:
        print(f"  Average actual FPPG: {analysis['avg_actual']:.1f}")
        print(f"  Average conservative projection: {analysis['avg_projected']:.1f}")
    
    print()
    
    # Lineup performance
    if lineup_performance:
        print(f"CONSERVATIVE LINEUP SIMULATION:")
        print(f"  Players in lineup: {lineup_performance['total_players']}")
        print(f"  Players found in results: {lineup_performance['players_found']}")
        print(f"  Total projected FPPG: {lineup_performance['total_projected']:.1f}")
        print(f"  Total actual FPPG: {lineup_performance['total_actual']:.1f}")
        print(f"  Performance accuracy: {lineup_performance['accuracy_pct']:.1f}%")
        
        print()
        print("LINEUP BREAKDOWN:")
        for player in lineup_performance['lineup_details']:
            status = "" if player['found'] else ""
            print(f"  {status} {player['player_name']:<20} {player['position']:<4} "
                  f"${player['salary']:>5} | Proj: {player['projected_fppg']:>5.1f} | "
                  f"Actual: {player['actual_fppg']:>5.1f}")
    
    print()
    print("ANALYSIS INSIGHTS:")
    
    if analysis['match_rate'] < 50:
        print("  WARNING: Low player match rate suggests date mismatch or data issues")
    else:
        print("   Good player match rate for analysis")
    
    if lineup_performance and lineup_performance['accuracy_pct'] > 80:
        print("   Conservative projections showing good accuracy")
    elif lineup_performance:
        print("  WARNING: Conservative projections may need adjustment")
    
    print()
    print("This backtest validates our conservative approach against")
    print("actual historical performance data.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Stack Performance Analysis for August 21st, 2025
Compare actual lineups against optimal results
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import sys

def analyze_player_performance():
    """Analyze how your players actually performed"""
    
    # Load actual results
    actual_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250821.csv"
    
    if not os.path.exists(actual_file):
        print(f"❌ Actual results file not found: {actual_file}")
        return None
        
    actual_df = pd.read_csv(actual_file)
    print(f"✅ Loaded actual results: {len(actual_df)} players")
    
    # Load your lineups
    lineup_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Enhanced_Lineups_FD_Format_20250821_135239.csv"
    
    if not os.path.exists(lineup_file):
        print(f"❌ Lineup file not found: {lineup_file}")
        return None
        
    lineups_df = pd.read_csv(lineup_file)
    print(f"✅ Loaded your lineups: {len(lineups_df)} lineups")
    
    # Analyze each lineup
    results = []
    
    for idx, lineup in lineups_df.iterrows():
        lineup_analysis = {
            'lineup_id': lineup['Lineup_ID'],
            'contest_type': lineup['Contest_Type'],
            'projected_total': lineup['Total_Projection'],
            'salary_used': lineup['Total_Salary'],
            'actual_total': 0,
            'players': [],
            'stack_teams': {},
            'best_players': []
        }
        
        # Extract player IDs and positions
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        
        for pos in positions:
            if pd.notna(lineup[pos]) and lineup[pos] != '':
                # Parse FanDuel format: 119663-52198:Lucas Giolito
                player_info = lineup[pos].split(':')
                if len(player_info) == 2:
                    player_id = player_info[0].split('-')[1]  # Get the actual player ID
                    player_name = player_info[1]
                    
                    # Find actual performance by name (more reliable than ID matching)
                    player_actual = actual_df[actual_df['name'].str.contains(player_name, case=False, na=False)]
                    
                    if len(player_actual) > 0:
                        actual_points = player_actual.iloc[0]['fanduel_points']
                        team = player_actual.iloc[0]['team']
                        
                        lineup_analysis['actual_total'] += actual_points
                        lineup_analysis['players'].append({
                            'name': player_name,
                            'position': pos,
                            'team': team,
                            'actual_points': actual_points
                        })
                        
                        # Track team stacks
                        if team not in lineup_analysis['stack_teams']:
                            lineup_analysis['stack_teams'][team] = 0
                        lineup_analysis['stack_teams'][team] += 1
                        
                        # Track best performers
                        if actual_points >= 15:  # Good performance threshold
                            lineup_analysis['best_players'].append({
                                'name': player_name,
                                'points': actual_points,
                                'team': team
                            })
                    else:
                        print(f"⚠️ Player not found in results: {player_name} (ID: {player_id})")
        
        # Calculate performance metrics
        lineup_analysis['projection_accuracy'] = (lineup_analysis['actual_total'] / lineup_analysis['projected_total']) * 100 if lineup_analysis['projected_total'] > 0 else 0
        lineup_analysis['points_vs_projection'] = lineup_analysis['actual_total'] - lineup_analysis['projected_total']
        
        results.append(lineup_analysis)
    
    return results

def find_optimal_stacks():
    """Find the best performing stacks from August 21st"""
    
    actual_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250821.csv"
    actual_df = pd.read_csv(actual_file)
    
    # Group by team to find best stacks
    team_performance = actual_df.groupby('team').agg({
        'fanduel_points': ['sum', 'mean', 'count', 'max'],
        'name': lambda x: list(x)
    }).round(2)
    
    team_performance.columns = ['total_points', 'avg_points', 'player_count', 'best_player_points', 'players']
    team_performance = team_performance.sort_values('total_points', ascending=False)
    
    return team_performance

def main():
    print("🏆 STACK PERFORMANCE ANALYSIS - August 21st, 2025")
    print("=" * 60)
    
    # Analyze your lineup performance
    results = analyze_player_performance()
    
    if not results:
        print("❌ Unable to complete analysis")
        return
    
    # Sort by actual performance
    results.sort(key=lambda x: x['actual_total'], reverse=True)
    
    print("\n📊 YOUR LINEUP PERFORMANCE:")
    print("-" * 40)
    
    best_lineup = None
    worst_lineup = None
    total_actual = 0
    total_projected = 0
    
    for i, lineup in enumerate(results[:10], 1):  # Show top 10
        performance_icon = "🔥" if lineup['actual_total'] >= 100 else "📈" if lineup['actual_total'] >= 80 else "📊"
        
        print(f"{performance_icon} {lineup['lineup_id']}")
        print(f"   Actual: {lineup['actual_total']:.1f} pts | Projected: {lineup['projected_total']:.1f} pts")
        print(f"   Accuracy: {lineup['projection_accuracy']:.1f}% | Diff: {lineup['points_vs_projection']:+.1f}")
        
        # Show main stack
        if lineup['stack_teams']:
            main_stack = max(lineup['stack_teams'].items(), key=lambda x: x[1])
            print(f"   Main Stack: {main_stack[0]} ({main_stack[1]} players)")
        
        # Show best performers
        if lineup['best_players']:
            best_names = [f"{p['name']} ({p['points']:.1f})" for p in sorted(lineup['best_players'], key=lambda x: x['points'], reverse=True)[:2]]
            print(f"   Stars: {', '.join(best_names)}")
        
        print()
        
        total_actual += lineup['actual_total']
        total_projected += lineup['projected_total']
        
        if i == 1:
            best_lineup = lineup
        if i == len(results):
            worst_lineup = lineup
    
    # Overall performance summary
    avg_actual = total_actual / len(results)
    avg_projected = total_projected / len(results)
    overall_accuracy = (avg_actual / avg_projected) * 100 if avg_projected > 0 else 0
    
    print("📈 OVERALL PERFORMANCE SUMMARY:")
    print("-" * 40)
    print(f"Total Lineups Analyzed: {len(results)}")
    print(f"Average Actual Score: {avg_actual:.1f} pts")
    print(f"Average Projected Score: {avg_projected:.1f} pts")
    print(f"Overall Accuracy: {overall_accuracy:.1f}%")
    print(f"Best Lineup: {best_lineup['lineup_id'] if best_lineup else 'N/A'} ({best_lineup['actual_total']:.1f} pts)" if best_lineup else "")
    
    # Find optimal stacks
    print("\n🏆 OPTIMAL STACKS FROM AUGUST 21st:")
    print("-" * 40)
    
    optimal_stacks = find_optimal_stacks()
    
    for i, (team, data) in enumerate(optimal_stacks.head(8).iterrows(), 1):
        stack_icon = "👑" if i <= 3 else "⭐"
        print(f"{stack_icon} #{i} {team}: {data['total_points']:.1f} total pts ({data['avg_points']:.1f} avg, {data['player_count']} players)")
        
        # Show top performers from this team
        team_players = optimal_stacks.loc[team, 'players']
        if isinstance(team_players, list) and len(team_players) > 0:
            actual_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250821.csv"
            actual_df = pd.read_csv(actual_file)
            team_df = actual_df[actual_df['team'] == team].sort_values('fanduel_points', ascending=False)
            top_3 = team_df.head(3)
            
            performers = []
            for _, player in top_3.iterrows():
                performers.append(f"{player['name']} ({player['fanduel_points']:.1f})")
            
            print(f"   Top: {', '.join(performers)}")
        print()
    
    # Stack comparison
    print("🎯 YOUR STACK CHOICES vs OPTIMAL:")
    print("-" * 40)
    
    # Analyze your main stacks
    your_stacks = {}
    for lineup in results:
        if lineup['stack_teams']:
            main_team = max(lineup['stack_teams'].items(), key=lambda x: x[1])[0]
            if main_team not in your_stacks:
                your_stacks[main_team] = []
            your_stacks[main_team].append(lineup['actual_total'])
    
    for team, scores in your_stacks.items():
        if team in optimal_stacks.index:
            optimal_rank = list(optimal_stacks.index).index(team) + 1
            avg_score = sum(scores) / len(scores)
            optimal_total = optimal_stacks.loc[team, 'total_points']
            
            status = "✅ GREAT" if optimal_rank <= 3 else "📊 OK" if optimal_rank <= 6 else "⚠️ POOR"
            print(f"{status} {team} Stack:")
            print(f"   Your avg: {avg_score:.1f} pts | Optimal rank: #{optimal_rank} | Team total: {optimal_total:.1f} pts")
            print(f"   Used in {len(scores)} lineup(s)")
            print()

if __name__ == "__main__":
    main()

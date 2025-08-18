#!/usr/bin/env python3
"""
working_lineup_generator.py
Lineup generator that respects salary cap and diversifies players
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random

def generate_working_lineups():
    """Generate lineups that stay under salary cap"""
    
    print("LINEUP: WORKING LINEUP GENERATOR")
    print("=" * 50)
    
    # Load slate with conservative projections
    slate_file = "../data/fd_slate_conservative_projections.csv"
    df = pd.read_csv(slate_file)
    
    print(f"DATA: Loaded {len(df)} players from today's slate")
    
    # Simplify positions for easier lineup building
    df = simplify_positions(df)
    
    # Show simplified position breakdown
    print(f"\nINFO: SIMPLIFIED POSITION BREAKDOWN:")
    position_counts = df['Simple_Position'].value_counts()
    for pos, count in position_counts.items():
        print(f"   {pos}: {count} players")
    
    lineups = []
    
    # Generate 10 lineups with different strategies
    for i in range(10):
        lineup = build_smart_lineup(df, i + 1)
        if lineup:
            lineups.append(lineup)
    
    if lineups:
        save_working_lineups(lineups)
        print(f"\nSUCCESS: Successfully generated {len(lineups)} working lineups!")
        
        # Show summary
        print(f"\nLINEUP: LINEUP SUMMARY:")
        for lineup in lineups:
            print(f"   {lineup['lineup_id']}: ${lineup['total_salary']:,} salary, {lineup['projected_fppg']:.1f} FPPG")
        
        avg_salary = sum(l['total_salary'] for l in lineups) / len(lineups)
        avg_fppg = sum(l['projected_fppg'] for l in lineups) / len(lineups)
        print(f"\nDATA: AVERAGES: ${avg_salary:,.0f} salary, {avg_fppg:.1f} FPPG")
        
    else:
        print("ERROR: Failed to generate any lineups")

def simplify_positions(df):
    """Simplify multi-position players to primary positions"""
    
    df = df.copy()
    
    def get_simple_position(pos):
        if pd.isna(pos):
            return 'UTIL'
        
        pos = str(pos).upper()
        
        # Pitchers
        if 'P' in pos:
            return 'P'
        
        # Catchers
        if pos.startswith('C'):
            return 'C'
        
        # Infielders - use first position listed
        if '1B' in pos:
            return '1B'
        if '2B' in pos:
            return '2B'
        if '3B' in pos:
            return '3B'
        if 'SS' in pos:
            return 'SS'
        
        # Outfielders
        if any(of_pos in pos for of_pos in ['OF', 'LF', 'CF', 'RF']):
            return 'OF'
        
        return 'UTIL'
    
    df['Simple_Position'] = df['Position'].apply(get_simple_position)
    
    return df

def build_smart_lineup(df, lineup_num):
    """Build a lineup that stays under salary cap"""
    
    salary_cap = 35000
    
    # Add randomization for diversity
    random.seed(42 + lineup_num * 7)
    
    try:
        selected_players = []
        total_salary = 0
        total_fppg = 0
        
        # Strategy: Start with budget players and build up
        remaining_salary = salary_cap
        
        # 1. Select budget Pitcher first (save money for hitters)
        pitchers = df[df['Simple_Position'] == 'P'].copy()
        if len(pitchers) == 0:
            return None
        
        # Pick from cheaper pitchers to save salary
        budget_pitchers = pitchers.nsmallest(min(10, len(pitchers)), 'Salary')
        pitcher = budget_pitchers.sample(1).iloc[0]
        
        selected_players.append(pitcher)
        total_salary += pitcher['Salary']
        total_fppg += pitcher['Conservative_FPPG']
        remaining_salary -= pitcher['Salary']
        
        # 2. Select budget Catcher
        catchers = df[df['Simple_Position'] == 'C'].copy()
        if len(catchers) > 0:
            affordable_catchers = catchers[catchers['Salary'] <= remaining_salary * 0.2]
            if len(affordable_catchers) == 0:
                affordable_catchers = catchers.nsmallest(3, 'Salary')
            
            catcher = affordable_catchers.sample(1).iloc[0]
            selected_players.append(catcher)
            total_salary += catcher['Salary']
            total_fppg += catcher['Conservative_FPPG']
            remaining_salary -= catcher['Salary']
        
        # 3. Fill infield positions with value picks
        infield_positions = ['1B', '2B', '3B', 'SS']
        
        for pos in infield_positions:
            pos_players = df[df['Simple_Position'] == pos].copy()
            if len(pos_players) == 0:
                continue
            
            # Find affordable players for this position
            budget_per_remaining = remaining_salary / (len(infield_positions) + 3)  # 3 OF remaining
            affordable = pos_players[pos_players['Salary'] <= budget_per_remaining * 1.2]
            
            if len(affordable) == 0:
                affordable = pos_players.nsmallest(5, 'Salary')
            
            # Pick best value from affordable options
            affordable['value_score'] = affordable['Conservative_FPPG'] / (affordable['Salary'] / 1000)
            player = affordable.nlargest(1, 'value_score').iloc[0]
            
            selected_players.append(player)
            total_salary += player['Salary']
            total_fppg += player['Conservative_FPPG']
            remaining_salary -= player['Salary']
        
        # 4. Fill outfield with remaining budget
        outfielders = df[df['Simple_Position'] == 'OF'].copy()
        if len(outfielders) < 3:
            return None
        
        # Budget per OF position
        of_budget = remaining_salary / 3
        
        selected_of_count = 0
        for _ in range(3):
            if selected_of_count >= 3:
                break
            
            # Remove already selected players
            available_of = outfielders.copy()
            for selected in selected_players:
                if 'ID' in selected:
                    available_of = available_of[available_of['ID'] != selected['ID']]
            
            if len(available_of) == 0:
                break
            
            # Find affordable OF
            affordable_of = available_of[available_of['Salary'] <= of_budget * 1.5]
            if len(affordable_of) == 0:
                affordable_of = available_of.nsmallest(3, 'Salary')
            
            # Pick best value
            affordable_of['value_score'] = affordable_of['Conservative_FPPG'] / (affordable_of['Salary'] / 1000)
            of_player = affordable_of.nlargest(1, 'value_score').iloc[0]
            
            selected_players.append(of_player)
            total_salary += of_player['Salary']
            total_fppg += of_player['Conservative_FPPG']
            remaining_salary -= of_player['Salary']
            selected_of_count += 1
            
            # Update budget for remaining OF
            if selected_of_count < 3:
                of_budget = remaining_salary / (3 - selected_of_count)
        
        # Validate lineup
        if len(selected_players) == 9 and total_salary <= salary_cap:
            print(f"SUCCESS: Lineup {lineup_num}: 9 players, ${total_salary:,} salary, {total_fppg:.1f} FPPG")
            return {
                'lineup_id': f'lineup_{lineup_num}',
                'players': selected_players,
                'total_salary': total_salary,
                'projected_fppg': total_fppg
            }
        else:
            print(f"WARNING: Lineup {lineup_num}: {len(selected_players)} players, ${total_salary:,} salary")
            return None
            
    except Exception as e:
        print(f"ERROR: Error building lineup {lineup_num}: {e}")
        return None

def save_working_lineups(lineups):
    """Save lineups in working format"""
    
    details_data = []
    summary_data = []
    
    for lineup in lineups:
        lineup_id = lineup['lineup_id']
        
        for i, player in enumerate(lineup['players']):
            details_data.append({
                'lineup_id': lineup_id,
                'player_name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Simple_Position'],
                'team': player.get('Team', 'UNK'),
                'salary': player['Salary'],
                'projected_fppg': player['Conservative_FPPG'],
                'ownership': 15.0
            })
        
        summary_data.append({
            'lineup_id': lineup_id,
            'projected_fppg': lineup['projected_fppg'],
            'total_salary': lineup['total_salary'],
            'accuracy_pct': 0,
            'actual_fppg': 0,
            'players_found': 0
        })
    
    # Save files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    details_df = pd.DataFrame(details_data)
    details_file = f"../data/working_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"../data/working_lineup_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    
    print(f"SUCCESS: Saved working lineup details: {details_file}")
    print(f"SUCCESS: Saved working lineup summary: {summary_file}")
    
    return details_file, summary_file

if __name__ == "__main__":
    generate_working_lineups()

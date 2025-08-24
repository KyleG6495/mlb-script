#!/usr/bin/env python3
"""
simple_conservative_lineup_generator.py
Simple lineup generator using current slate with conservative projections
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random

def generate_conservative_lineups():
    """Generate conservative lineups for today's slate"""
    
    print("LINEUP: CONSERVATIVE LINEUP GENERATOR")
    print("=" * 50)
    
    # Load slate with conservative projections
    slate_file = "../data/fd_slate_conservative_projections.csv"
    df = pd.read_csv(slate_file)
    
    print(f"DATA: Loaded {len(df)} players from today's slate")
    
    # Show position breakdown
    print(f"\nINFO: POSITION BREAKDOWN:")
    position_counts = df['Position'].value_counts()
    for pos, count in position_counts.items():
        print(f"   {pos}: {count} players")
    
    lineups = []
    
    # Generate 10 diversified lineups
    for i in range(10):
        lineup = build_lineup(df, i + 1)
        if lineup:
            lineups.append(lineup)
    
    if lineups:
        save_conservative_lineups(lineups)
        print(f"\nSUCCESS: Successfully generated {len(lineups)} conservative lineups!")
        
        # Show summary
        print(f"\nLINEUP: LINEUP SUMMARY:")
        for lineup in lineups:
            print(f"   {lineup['lineup_id']}: ${lineup['total_salary']:,} salary, {lineup['projected_fppg']:.1f} FPPG")
        
        avg_salary = sum(l['total_salary'] for l in lineups) / len(lineups)
        avg_fppg = sum(l['projected_fppg'] for l in lineups) / len(lineups)
        print(f"\nDATA: AVERAGES: ${avg_salary:,.0f} salary, {avg_fppg:.1f} FPPG")
        
    else:
        print("ERROR: Failed to generate any lineups")

def build_lineup(df, lineup_num):
    """Build a single conservative lineup"""
    
    salary_cap = 35000
    total_salary = 0
    total_fppg = 0
    selected_players = []
    
    # Add some randomization for diversity
    random.seed(42 + lineup_num * 13)
    
    try:
        # 1. Select Pitcher (P)
        pitchers = df[df['Position'] == 'P'].copy()
        if len(pitchers) == 0:
            return None
        
        # Pick from top pitchers with some randomization
        top_pitchers = pitchers.nlargest(min(8, len(pitchers)), 'Conservative_FPPG')
        pitcher = top_pitchers.sample(1).iloc[0]
        
        selected_players.append(pitcher)
        total_salary += pitcher['Salary']
        total_fppg += pitcher['Conservative_FPPG']
        
        # 2. Select Catcher (C)
        catchers = df[df['Position'] == 'C'].copy()
        if len(catchers) > 0:
            # Pick budget catcher to save salary
            budget_catchers = catchers.nsmallest(min(5, len(catchers)), 'Salary')
            catcher = budget_catchers.sample(1).iloc[0]
            
            selected_players.append(catcher)
            total_salary += catcher['Salary']
            total_fppg += catcher['Conservative_FPPG']
        
        # 3. Select Infielders (1B, 2B, 3B, SS)
        infield_positions = ['1B', '2B', '3B', 'SS']
        
        for pos in infield_positions:
            pos_players = df[df['Position'] == pos].copy()
            if len(pos_players) == 0:
                continue
            
            # Pick from top players for this position
            top_players = pos_players.nlargest(min(6, len(pos_players)), 'Conservative_FPPG')
            player = top_players.sample(1).iloc[0]
            
            selected_players.append(player)
            total_salary += player['Salary']
            total_fppg += player['Conservative_FPPG']
        
        # 4. Select Outfielders (need 3)
        outfielders = df[df['Position'].isin(['OF', 'LF', 'CF', 'RF'])].copy()
        if len(outfielders) < 3:
            return None
        
        # Pick 3 different outfielders
        top_outfielders = outfielders.nlargest(min(10, len(outfielders)), 'Conservative_FPPG')
        selected_of = top_outfielders.sample(min(3, len(top_outfielders)))
        
        for _, of_player in selected_of.iterrows():
            selected_players.append(of_player)
            total_salary += of_player['Salary']
            total_fppg += of_player['Conservative_FPPG']
        
        # Validate lineup
        if len(selected_players) == 9 and total_salary <= salary_cap:
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

def save_conservative_lineups(lineups):
    """Save lineups in the expected format"""
    
    details_data = []
    summary_data = []
    
    for lineup in lineups:
        lineup_id = lineup['lineup_id']
        
        for _, player in enumerate(lineup['players']):
            details_data.append({
                'lineup_id': lineup_id,
                'player_name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Position'],
                'team': player.get('Team', 'UNK'),
                'salary': player['Salary'],
                'projected_fppg': player['Conservative_FPPG'],
                'ownership': 15.0  # Default conservative ownership estimate
            })
        
        summary_data.append({
            'lineup_id': lineup_id,
            'projected_fppg': lineup['projected_fppg'],
            'total_salary': lineup['total_salary'],
            'accuracy_pct': 0,  # Will be calculated during backtest
            'actual_fppg': 0,   # Will be filled during backtest
            'players_found': 0  # Will be filled during backtest
        })
    
    # Save files with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    details_df = pd.DataFrame(details_data)
    details_file = f"../data/conservative_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"../data/conservative_lineup_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    
    # Also create FanDuel submission format
    fanduel_data = []
    for lineup in lineups:
        lineup_players = []
        for _, player in enumerate(lineup['players']):
            player_name = f"{player['First Name']} {player['Last Name']}"
            lineup_players.append(player_name)
        
        # Ensure 9 players
        while len(lineup_players) < 9:
            lineup_players.append("")
        
        fanduel_data.append({
            'P': lineup_players[0] if len(lineup_players) > 0 else "",
            'C/1B': lineup_players[1] if len(lineup_players) > 1 else "",
            '2B': lineup_players[2] if len(lineup_players) > 2 else "",
            '3B': lineup_players[3] if len(lineup_players) > 3 else "",
            'SS': lineup_players[4] if len(lineup_players) > 4 else "",
            'OF': lineup_players[5] if len(lineup_players) > 5 else "",
            'OF ': lineup_players[6] if len(lineup_players) > 6 else "",
            'OF  ': lineup_players[7] if len(lineup_players) > 7 else "",
            'UTIL': lineup_players[8] if len(lineup_players) > 8 else ""
        })
    
    fanduel_df = pd.DataFrame(fanduel_data)
    fanduel_file = f"../data/conservative_lineups_fanduel_{timestamp}.csv"
    fanduel_df.to_csv(fanduel_file, index=False)
    
    print(f"SUCCESS: Saved conservative lineup details: {details_file}")
    print(f"SUCCESS: Saved conservative lineup summary: {summary_file}")
    print(f"SUCCESS: Saved FanDuel submission format: {fanduel_file}")
    
    return details_file, summary_file, fanduel_file

if __name__ == "__main__":
    generate_conservative_lineups()

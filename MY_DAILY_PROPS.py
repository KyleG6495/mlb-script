#!/usr/bin/env python3
"""
MY DAILY PROP BET INPUT SYSTEM
=============================
Quick way to input your prop bet decisions and generate lineups based on your picks.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def input_my_props():
    """Input your daily prop bet decisions"""
    print("TARGET: DAILY PROP BET INPUT SYSTEM")
    print("=" * 50)
    print("Enter your prop bet decisions for today's slate")
    print("Format: Player Name, Prop Type, Line, Your Pick (Over/Under), Confidence (1-5)")
    print("Example: Aaron Judge, Home Runs, 1.5, Over, 4")
    print("Type 'done' when finished")
    print()
    
    props = []
    
    while True:
        prop_input = input("Enter prop (or 'done'): ").strip()
        
        if prop_input.lower() == 'done':
            break
            
        try:
            parts = [p.strip() for p in prop_input.split(',')]
            if len(parts) != 5:
                print("ERROR: Invalid format. Use: Player, Prop Type, Line, Pick, Confidence")
                continue
                
            player, prop_type, line, pick, confidence = parts
            
            props.append({
                'player_name': player,
                'prop_type': prop_type,
                'line': float(line),
                'my_pick': pick.upper(),
                'confidence': int(confidence),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            print(f"SUCCESS: Added: {player} {prop_type} {line} {pick} (Confidence: {confidence})")
            
        except Exception as e:
            print(f"ERROR: Error: {e}")
            print("Please use format: Player Name, Prop Type, Line, Your Pick, Confidence")
    
    return pd.DataFrame(props)

def save_my_props(props_df):
    """Save your prop decisions"""
    if len(props_df) == 0:
        print("ERROR: No props to save")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/my_daily_props_{timestamp}.csv"
    
    props_df.to_csv(filename, index=False)
    print(f" Saved your props: {filename}")
    return filename

def load_my_latest_props():
    """Load your most recent prop decisions"""
    import glob
    
    prop_files = glob.glob("../data/my_daily_props_*.csv")
    
    if not prop_files:
        print("ERROR: No prop files found. Run input mode first.")
        return None
    
    latest_file = max(prop_files)
    props_df = pd.read_csv(latest_file)
    
    print(f"DATA: Loaded {len(props_df)} props from {latest_file}")
    return props_df

def generate_lineups_from_my_props(props_df):
    """Generate DFS lineups based on your prop decisions"""
    
    if props_df is None or len(props_df) == 0:
        print("ERROR: No props available for lineup generation")
        return
    
    print("\nLINEUP: GENERATING LINEUPS FROM YOUR PROPS")
    print("=" * 50)
    
    # Load current slate
    try:
        slate_df = pd.read_csv("../data/fd_slate_starters_only.csv")
        print(f"SUCCESS: Loaded {len(slate_df)} players from slate")
    except:
        print("ERROR: Could not load fd_slate_today.csv")
        return
    
    # Filter to confirmed starters (your proven system)
    pitchers = slate_df[slate_df['Position'] == 'P']
    starting_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
    
    hitters = slate_df[slate_df['Position'] != 'P'] 
    starting_hitters = hitters[hitters['Batting Order'].notna() & (hitters['Batting Order'] != '')]
    
    confirmed_starters = pd.concat([starting_pitchers, starting_hitters], ignore_index=True)
    confirmed_starters['player_name'] = confirmed_starters['First Name'] + ' ' + confirmed_starters['Last Name']
    
    print(f"TARGET: Filtered to {len(confirmed_starters)} confirmed starters")
    
    # Boost players based on your prop confidence
    for _, prop in props_df.iterrows():
        player_matches = confirmed_starters[
            confirmed_starters['player_name'].str.contains(prop['player_name'], case=False, na=False)
        ]
        
        if len(player_matches) > 0:
            # Boost FPPG based on your confidence (1-5 scale)
            boost_factor = 1 + (prop['confidence'] * 0.1)  # 10% boost per confidence point
            
            confirmed_starters.loc[
                confirmed_starters['player_name'].str.contains(prop['player_name'], case=False, na=False),
                'FPPG'
            ] *= boost_factor
            
            print(f"START: Boosted {prop['player_name']} by {(boost_factor-1)*100:.0f}% (confidence {prop['confidence']})")
    
    # Generate lineups using your proven system
    print("\nLINEUP: Building lineups with your prop boosts...")
    
    # Use DAILY_LINEUP_GENERATOR logic but with prop-boosted projections
    lineups = []
    
    for i in range(1, 6):  # Generate 5 lineups
        lineup = build_prop_based_lineup(confirmed_starters.copy(), i)
        if lineup:
            lineups.append(lineup)
    
    # Save results
    if lineups:
        save_prop_based_lineups(lineups, props_df)
        print(f"\nSUCCESS: Generated {len(lineups)} lineups based on your props!")
    else:
        print("ERROR: Could not generate lineups")

def build_prop_based_lineup(slate_df, strategy_num):
    """Build lineup with prop-based player boosts"""
    
    np.random.seed(strategy_num * 23)
    
    lineup = []
    remaining_salary = 35000
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Expand multi-position eligibility
    expanded_slate = []
    for _, player in slate_df.iterrows():
        positions_eligible = player['Position'].split('/')
        for pos in positions_eligible:
            if pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                new_row = player.copy()
                new_row['Position'] = pos
                expanded_slate.append(new_row)
    
    slate_df = pd.DataFrame(expanded_slate)
    
    for pos in positions:
        available = slate_df[slate_df['Position'] == pos].copy()
        
        if len(available) == 0:
            return None
            
        affordable = available[available['Salary'] <= remaining_salary]
        
        if len(affordable) == 0:
            affordable = available.nsmallest(1, 'Salary')
        
        # Prioritize prop-boosted players
        affordable = affordable.copy()  # Fix pandas warning
        affordable['prop_score'] = affordable['FPPG'] / affordable['Salary'] * 1000
        chosen = affordable.nlargest(1, 'prop_score').iloc[0]
        
        lineup.append({
            'player_name': chosen['First Name'] + ' ' + chosen['Last Name'],
            'position': chosen['Position'],
            'team': chosen['Team'],
            'salary': chosen['Salary'],
            'projected_fppg': chosen['FPPG']
        })
        
        remaining_salary -= chosen['Salary']
        slate_df = slate_df[slate_df.index != chosen.name]
    
    return lineup

def save_prop_based_lineups(lineups, props_df):
    """Save lineups generated from your props"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # FanDuel format
    fd_lineups = []
    for i, lineup in enumerate(lineups):
        fd_row = {'Lineup': f"prop_lineup_{i+1}"}
        
        for player in lineup:
            pos = player['position']
            if pos == 'OF':
                of_count = sum(1 for p in lineup[:lineup.index(player)] if p['position'] == 'OF')
                pos = f"OF{of_count + 1}"
            
            fd_row[pos] = f"{player['player_name']} ({player['team']})"
        
        fd_row['Total_Salary'] = sum(p['salary'] for p in lineup)
        fd_row['Projected_FPPG'] = sum(p['projected_fppg'] for p in lineup)
        
        fd_lineups.append(fd_row)
    
    # Save FanDuel format
    fd_df = pd.DataFrame(fd_lineups)
    fd_file = f"../data/prop_based_lineups_{timestamp}.csv"
    fd_df.to_csv(fd_file, index=False)
    
    # Save prop summary
    props_file = f"../data/prop_summary_{timestamp}.csv" 
    props_df.to_csv(props_file, index=False)
    
    print(f" Prop-based lineups: {fd_file}")
    print(f" Your props summary: {props_file}")

def main():
    """Main function for prop-based lineup generation"""
    
    print("TARGET: MY DAILY PROP BET SYSTEM")
    print("=" * 40)
    print("Choose an option:")
    print("1. Input new prop bets")
    print("2. Generate lineups from existing props")
    print("3. View my recent props")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        # Input new props
        props_df = input_my_props()
        save_my_props(props_df)
        
        # Ask if they want lineups now
        if len(props_df) > 0:
            gen_now = input("\nGenerate lineups now? (y/n): ").strip().lower()
            if gen_now == 'y':
                generate_lineups_from_my_props(props_df)
    
    elif choice == '2':
        # Generate from existing props
        props_df = load_my_latest_props()
        generate_lineups_from_my_props(props_df)
    
    elif choice == '3':
        # View recent props
        props_df = load_my_latest_props()
        if props_df is not None:
            print("\nDATA: YOUR RECENT PROPS:")
            print(props_df.to_string(index=False))
    
    else:
        print("ERROR: Invalid choice")

if __name__ == "__main__":
    main()

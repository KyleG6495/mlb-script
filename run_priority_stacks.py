#!/usr/bin/env python3
"""
PRIORITY STACKED LINEUP GENERATOR
Uses your excellent stack analysis to generate lineups with high-priority stacks
Focuses on BAL, STL, WSH stacks that were identified yesterday
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import os

def load_slate_data():
    """Load and clean today's slate data"""
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    slate_df = pd.read_csv(slate_file)
    
    # Clean and prepare data
    slate_df['Projected_FPPG'] = pd.to_numeric(slate_df['FPPG'], errors='coerce')
    slate_df['Salary'] = pd.to_numeric(slate_df['Salary'], errors='coerce')
    slate_df = slate_df.dropna(subset=['Projected_FPPG', 'Salary', 'Team'])
    
    print(f"✅ Loaded {len(slate_df)} players")
    return slate_df

def load_stack_analysis():
    """Load latest stack analysis"""
    data_dir = "../data"
    stack_files = [f for f in os.listdir(data_dir) if 'team_stack_analysis' in f and f.endswith('.csv')]
    
    if stack_files:
        latest_stack_file = max(stack_files)
        stack_df = pd.read_csv(f"{data_dir}/{latest_stack_file}")
        print(f"📈 Stack analysis: {latest_stack_file}")
        print("Top 5 stacks:")
        for i, row in stack_df.head().iterrows():
            print(f"  {i+1}. {row['team']}: {row['stack_value_score']:.2f} score vs {row['opposing_pitcher']}")
        return stack_df
    else:
        print("⚠️ No stack analysis found!")
        return pd.DataFrame()

def generate_stack_lineups(slate_df, stack_df, target_teams=['BAL', 'STL', 'WSH']):
    """Generate lineups focusing on high-priority teams"""
    
    lineups = []
    
    for target_team in target_teams:
        print(f"\n🎯 Building {target_team} stack lineup...")
        
        # Get team players
        team_hitters = slate_df[
            (slate_df['Team'] == target_team) & 
            (slate_df['Position'] != 'P')
        ].copy()
        
        if len(team_hitters) < 3:
            print(f"❌ Not enough {target_team} hitters available")
            continue
        
        # Sort by value (FPPG per $1000 salary)
        team_hitters['value'] = team_hitters['Projected_FPPG'] / team_hitters['Salary'] * 1000
        team_hitters = team_hitters.sort_values('value', ascending=False)
        
        print(f"📊 {target_team} hitters available: {len(team_hitters)}")
        print("Top 3 hitters:")
        for i, (_, player) in enumerate(team_hitters.head(3).iterrows()):
            print(f"  {i+1}. {player['Nickname']} ({player['Position']}): {player['Projected_FPPG']:.1f} pts, ${player['Salary']:,}")
        
        # Build optimal lineup with team stack
        lineup = build_optimal_stack_lineup(slate_df, target_team, min_stack_size=3)
        
        if lineup is not None:
            lineups.append({
                'lineup': lineup,
                'target_team': target_team,
                'stack_size': len(lineup[lineup['Team'] == target_team])
            })
            print(f"✅ {target_team} stack lineup generated!")
        else:
            print(f"❌ Failed to generate {target_team} stack lineup")
    
    return lineups

def build_optimal_stack_lineup(slate_df, target_team, min_stack_size=3):
    """Build optimal lineup with team stack constraint"""
    
    # Setup optimization problem
    prob = LpProblem(f"FD_Stack_{target_team}", LpMaximize)
    
    # Decision variables for each player
    player_vars = {}
    for idx, player in slate_df.iterrows():
        player_vars[idx] = LpVariable(f"player_{idx}", cat='Binary')
    
    # Objective: maximize projected FPPG
    objective = lpSum(slate_df.loc[idx, 'Projected_FPPG'] * player_vars[idx] for idx in slate_df.index)
    prob += objective
    
    # Constraint: exactly 9 players
    prob += lpSum(player_vars[idx] for idx in slate_df.index) == 9
    
    # Constraint: salary cap $35,000 (FanDuel)
    prob += lpSum(slate_df.loc[idx, 'Salary'] * player_vars[idx] for idx in slate_df.index) <= 35000
    
    # Position constraints (FanDuel format)
    position_requirements = {
        'P': 1,    # 1 Pitcher
        'C': 1,    # 1 Catcher 
        '1B': 1,   # 1 First Base
        '2B': 1,   # 1 Second Base
        '3B': 1,   # 1 Third Base
        'SS': 1,   # 1 Shortstop
        'OF': 3    # 3 Outfield
    }
    
    for pos, required in position_requirements.items():
        pos_players = slate_df[slate_df['Position'] == pos].index
        if len(pos_players) >= required:
            prob += lpSum(player_vars[idx] for idx in pos_players) == required
    
    # Team stack constraint: at least min_stack_size players from target team
    target_hitters = slate_df[
        (slate_df['Team'] == target_team) & 
        (slate_df['Position'] != 'P')
    ].index
    
    if len(target_hitters) >= min_stack_size:
        prob += lpSum(player_vars[idx] for idx in target_hitters) >= min_stack_size
    
    # Solve the problem
    solver = PULP_CBC_CMD(msg=False)
    status = prob.solve(solver)
    
    if status == 1:  # Optimal solution found
        # Extract selected players
        selected_indices = [idx for idx in slate_df.index if player_vars[idx].value() == 1]
        lineup_df = slate_df.loc[selected_indices].copy()
        
        # Verify lineup
        total_salary = lineup_df['Salary'].sum()
        total_projection = lineup_df['Projected_FPPG'].sum()
        stack_count = len(lineup_df[lineup_df['Team'] == target_team])
        
        print(f"   Salary: ${total_salary:,}, Projection: {total_projection:.1f}, Stack: {stack_count} {target_team} players")
        
        return lineup_df
    else:
        return None

def save_lineups(lineups):
    """Save generated lineups"""
    if not lineups:
        print("❌ No lineups to save!")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Combine all lineups with proper lineup numbering
    all_lineups = []
    for i, lineup_data in enumerate(lineups):
        lineup_df = lineup_data['lineup'].copy()
        lineup_df['Lineup_Number'] = i + 1
        lineup_df['Target_Team'] = lineup_data['target_team']
        lineup_df['Stack_Size'] = lineup_data['stack_size']
        lineup_df['Generated_At'] = timestamp
        all_lineups.append(lineup_df)
    
    combined_df = pd.concat(all_lineups, ignore_index=True)
    
    # Save full version
    output_file = f"../fd_current_slate/PRIORITY_STACKED_LINEUPS_{timestamp}.csv"
    combined_df.to_csv(output_file, index=False)
    
    # Save FanDuel format - dashboard compatible
    fd_columns = ['Nickname', 'Position', 'Team', 'Salary', 'Projected_FPPG', 'Lineup_Number', 'Target_Team']
    available_columns = [col for col in fd_columns if col in combined_df.columns]
    fd_format = combined_df[available_columns]
    
    fd_output = f"../fd_current_slate/PRIORITY_STACKED_LINEUPS_FD_{timestamp}.csv"
    fd_format.to_csv(fd_output, index=False)
    
    # Also save the most recent as a standard name for dashboard integration
    latest_output = "../fd_current_slate/LATEST_STACKED_LINEUPS.csv"
    fd_format.to_csv(latest_output, index=False)
    
    print(f"\n💾 Saved {len(lineups)} lineups:")
    print(f"   Full: PRIORITY_STACKED_LINEUPS_{timestamp}.csv")
    print(f"   FD Format: PRIORITY_STACKED_LINEUPS_FD_{timestamp}.csv")
    print(f"   Latest: LATEST_STACKED_LINEUPS.csv (for dashboard)")
    
    # Print lineup summaries
    for i, lineup_data in enumerate(lineups):
        lineup_df = lineup_data['lineup']
        target_team = lineup_data['target_team']
        stack_size = lineup_data['stack_size']
        total_proj = lineup_df['Projected_FPPG'].sum()
        total_salary = lineup_df['Salary'].sum()
        
        print(f"\n📋 Lineup {i+1} ({target_team} stack):")
        print(f"   Projection: {total_proj:.1f} pts, Salary: ${total_salary:,}")
        print(f"   {target_team} Stack ({stack_size} players):")
        
        stack_players = lineup_df[lineup_df['Team'] == target_team]
        for _, player in stack_players.iterrows():
            print(f"     • {player['Nickname']} ({player['Position']}): {player['Projected_FPPG']:.1f} pts")

def main():
    print("🔥 PRIORITY STACKED LINEUP GENERATOR")
    print("=" * 50)
    print("Focus: BAL, STL, WSH stacks (your top recommendations)")
    print()
    
    # Load data
    slate_df = load_slate_data()
    stack_df = load_stack_analysis()
    
    # Get priority teams from stack analysis
    if not stack_df.empty:
        top_teams = stack_df.head(5)['team'].tolist()
        print(f"\n🎯 Priority teams: {', '.join(top_teams)}")
    else:
        top_teams = ['BAL', 'STL', 'WSH']  # Default to yesterday's top stacks
    
    # Generate stacked lineups
    lineups = generate_stack_lineups(slate_df, stack_df, top_teams)
    
    # Save results
    save_lineups(lineups)
    
    if lineups:
        print(f"\n🏆 SUCCESS! Generated {len(lineups)} stacked lineups")
        print("These lineups have the team correlation that was missing yesterday!")
    else:
        print("\n❌ No lineups generated")

if __name__ == "__main__":
    main()

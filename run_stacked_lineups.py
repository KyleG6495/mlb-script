#!/usr/bin/env python3
"""
STACKED LINEUP GENERATOR
Uses existing stack analysis to create actual stacked lineups
Bridges the gap between stack analysis and lineup generation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from stacking_optimizer import StackingOptimizer
import os

def main():
    print("🏗️ STACKED LINEUP GENERATOR")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load today's slate
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    if not os.path.exists(slate_file):
        print("❌ No fd_slate_today.csv found!")
        return
    
    print("📊 Loading slate data...")
    slate_df = pd.read_csv(slate_file)
    print(f"✅ Loaded {len(slate_df)} players")
    
    # Load latest stack analysis
    data_dir = "../data"
    stack_files = [f for f in os.listdir(data_dir) if 'team_stack_analysis' in f and f.endswith('.csv')]
    if stack_files:
        latest_stack_file = max(stack_files)
        stack_df = pd.read_csv(f"{data_dir}/{latest_stack_file}")
        print(f"📈 Loaded stack analysis: {latest_stack_file}")
        print(f"Top stacks: {stack_df.head(3)['team'].tolist()}")
    else:
        print("⚠️ No stack analysis found!")
        stack_df = None
    
    # Prepare data for stacking optimizer
    # Map FanDuel columns to optimizer expected columns
    players = slate_df.copy()
    
    # Handle different possible column names
    if 'Position' in players.columns:
        players['Primary_Position'] = players['Position']
    elif 'Pos' in players.columns:
        players['Primary_Position'] = players['Pos']
    
    if 'FPPG' in players.columns:
        players['Projected_FPPG'] = pd.to_numeric(players['FPPG'], errors='coerce')
    elif 'Projected Points' in players.columns:
        players['Projected_FPPG'] = pd.to_numeric(players['Projected Points'], errors='coerce')
    else:
        # Estimate from salary if no projections
        players['Projected_FPPG'] = players['Salary'] / 300
    
    if 'Team' not in players.columns and 'Tm' in players.columns:
        players['Team'] = players['Tm']
    
    # Create Game identifier if not present
    if 'Game' not in players.columns:
        if 'Opponent' in players.columns:
            players['Game'] = players['Team'] + '@' + players['Opponent']
        else:
            players['Game'] = 'Unknown'
    
    # Clean data - remove NaN values and ensure numeric columns
    players['Salary'] = pd.to_numeric(players['Salary'], errors='coerce')
    players = players.dropna(subset=['Projected_FPPG', 'Salary', 'Team'])
    
    # Fill any remaining NaN values
    players['Projected_FPPG'] = players['Projected_FPPG'].fillna(players['Salary'] / 300)
    players['Salary'] = players['Salary'].fillna(5000)
    players['Team'] = players['Team'].fillna('UNK')
    
    print(f"🧹 Data cleaned. {len(players)} valid players remaining")
    
    print(f"📋 Data prep complete. Columns: {list(players.columns)}")
    
    # Initialize stacking optimizer
    stack_optimizer = StackingOptimizer(players)
    
    # Generate different types of stacked lineups
    lineup_types = [
        ('team_stack_3', 'Team Stack (3+ players)'),
        ('game_stack', 'Game Stack (high-scoring games)'),
    ]
    
    all_lineups = []
    
    for strategy, description in lineup_types:
        print(f"\n🎯 Generating {description}...")
        
        try:
            lineup, analysis = stack_optimizer.optimize_with_stacking(strategy)
            
            if lineup is not None:
                # Add strategy info
                lineup['Strategy'] = strategy
                lineup['Description'] = description
                lineup['Generated_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                all_lineups.append(lineup)
                
                print(f"✅ {description} lineup generated:")
                print(f"   Total Salary: ${lineup['Salary'].sum():,}")
                print(f"   Total Projection: {lineup['Projected_FPPG'].sum():.1f}")
                print(f"   Stacks: {analysis}")
                
                # Show the actual stack
                if analysis.get('team_stacks'):
                    for team, count in analysis['team_stacks'].items():
                        team_players = lineup[lineup['Team'] == team]
                        if len(team_players) >= 2:
                            print(f"   🔥 {team} Stack ({count} players): {', '.join(team_players['Nickname'].tolist())}")
            else:
                print(f"❌ Failed to generate {description} lineup")
                
        except Exception as e:
            print(f"❌ Error generating {description}: {e}")
    
    # Save all lineups
    if all_lineups:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Combine all lineups
        combined_lineups = pd.concat(all_lineups, ignore_index=True)
        
        # Save to fd_current_slate
        output_file = f"../fd_current_slate/STACKED_LINEUPS_{timestamp}.csv"
        combined_lineups.to_csv(output_file, index=False)
        print(f"\n💾 Saved {len(all_lineups)} stacked lineups to: STACKED_LINEUPS_{timestamp}.csv")
        
        # Also create FanDuel upload format
        fd_columns = ['Nickname', 'Position', 'Team', 'Salary', 'Projected_FPPG']
        available_columns = [col for col in fd_columns if col in combined_lineups.columns]
        
        fd_format = combined_lineups[available_columns]
        fd_output = f"../fd_current_slate/STACKED_LINEUPS_FD_FORMAT_{timestamp}.csv"
        fd_format.to_csv(fd_output, index=False)
        print(f"📤 FanDuel format saved to: STACKED_LINEUPS_FD_FORMAT_{timestamp}.csv")
        
        # Print lineup summary
        print(f"\n📊 LINEUP SUMMARY:")
        for i, lineup in enumerate(all_lineups, 1):
            strategy = lineup['Strategy'].iloc[0]
            proj = lineup['Projected_FPPG'].sum()
            salary = lineup['Salary'].sum()
            print(f"  Lineup {i} ({strategy}): {proj:.1f} pts, ${salary:,}")
    else:
        print("\n❌ No lineups generated!")

if __name__ == "__main__":
    main()

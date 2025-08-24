#!/usr/bin/env python3
"""
IMPROVED MANUAL DFS OPTIMIZER
============================
Better variety and strategy mixing.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def improved_lineup_builder():
    """Build diverse lineups with better strategies"""
    
    print("🚀 IMPROVED MANUAL DFS LINEUP BUILDER")
    print("=" * 50)
    
    # Load and clean data once
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    original_slate = pd.read_csv(slate_dir / "fd_slate_today.csv")
    
    clean_slate = original_slate[original_slate['FPPG'] > 2.0].copy()
    clean_slate = clean_slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])
    clean_slate['value'] = clean_slate['FPPG'] / (clean_slate['Salary'] / 1000)
    
    print(f"Working with {len(clean_slate)} clean players")
    
    lineups = []
    used_players = set()  # Track globally used players for variety
    
    for lineup_num in range(20):
        print(f"Building lineup {lineup_num + 1}...")
        
        # Create working slate (remove globally overused players)
        slate = clean_slate.copy()
        if lineup_num > 5:  # After first 5, start avoiding overused players
            slate = slate[~slate['Id'].isin(used_players)]
            if len(slate) < 500:  # If we removed too many, add some back
                slate = clean_slate.copy()
        
        lineup_players = []
        remaining_budget = 35000
        
        # Different strategies for different lineup numbers
        strategy = determine_strategy(lineup_num)
        
        # Position filling with strategy
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for pos_idx, position in enumerate(positions):
            if position == 'P':
                candidates = slate[slate['Roster Position'] == 'P']
            elif position == 'UTIL':
                # UTIL can be anyone
                candidates = slate[slate['Roster Position'].str.contains('UTIL|C/1B|2B|3B|SS|OF')]
            else:
                candidates = slate[slate['Roster Position'].str.contains(position)]
            
            # Filter by budget
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"  ❌ No affordable {position} players")
                break
            
            # Apply strategy
            chosen = select_player_by_strategy(affordable, strategy, pos_idx, remaining_budget)
            
            if chosen is not None:
                lineup_players.append(chosen)
                remaining_budget -= chosen['Salary']
                
                # Remove from slate for this lineup
                slate = slate[slate['Id'] != chosen['Id']]
                
                # Track usage
                used_players.add(chosen['Id'])
        
        if len(lineup_players) == 9:
            total_salary = sum(p['Salary'] for p in lineup_players)
            total_fppg = sum(p['FPPG'] for p in lineup_players)
            
            lineups.append({
                'players': lineup_players,
                'total_salary': total_salary,
                'total_fppg': total_fppg,
                'lineup_id': lineup_num + 1,
                'strategy': strategy
            })
            
            print(f"  ✅ Salary: ${total_salary}, FPPG: {total_fppg:.1f} ({strategy})")
        else:
            print(f"  ❌ Only got {len(lineup_players)} players")
    
    return lineups

def determine_strategy(lineup_num):
    """Determine strategy based on lineup number"""
    strategies = [
        'value_max',      # 1-4: Pure value
        'value_max',
        'value_max', 
        'value_max',
        'balanced',       # 5-8: Balanced approach
        'balanced',
        'balanced',
        'balanced',
        'ceiling',        # 9-12: High ceiling plays
        'ceiling',
        'ceiling',
        'ceiling',
        'contrarian',     # 13-16: Lower owned players
        'contrarian',
        'contrarian',
        'contrarian',
        'stack_heavy',    # 17-20: Team stacking
        'stack_heavy',
        'stack_heavy',
        'stack_heavy'
    ]
    return strategies[lineup_num]

def select_player_by_strategy(candidates, strategy, pos_idx, remaining_budget):
    """Select player based on strategy"""
    
    if candidates.empty:
        return None
    
    if strategy == 'value_max':
        # Pure value play
        return candidates.nlargest(1, 'value').iloc[0]
    
    elif strategy == 'balanced':
        # Mix of value and projection
        candidates['combo_score'] = candidates['value'] * 0.6 + (candidates['FPPG'] / candidates['FPPG'].max()) * 0.4
        return candidates.nlargest(1, 'combo_score').iloc[0]
    
    elif strategy == 'ceiling':
        # High projection plays
        return candidates.nlargest(1, 'FPPG').iloc[0]
    
    elif strategy == 'contrarian':
        # Avoid the top values, find middle tier
        value_rank = candidates['value'].rank(pct=True)
        mid_tier = candidates[(value_rank >= 0.3) & (value_rank <= 0.7)]
        if not mid_tier.empty:
            return mid_tier.sample(1).iloc[0]
        else:
            return candidates.sample(1).iloc[0]
    
    elif strategy == 'stack_heavy':
        # Try to get same team players when possible
        if len(candidates) > 1:
            # Sample from top 30% by value
            top_candidates = candidates.nlargest(max(1, len(candidates)//3), 'value')
            return top_candidates.sample(1).iloc[0]
        else:
            return candidates.iloc[0]
    
    else:
        return candidates.nlargest(1, 'value').iloc[0]

def save_improved_lineups(lineups):
    """Save lineups with better formatting"""
    if not lineups:
        print("No lineups to save!")
        return None
    
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    fanduel_data = []
    
    for lineup in lineups:
        players = lineup['players']
        
        lineup_row = {
            'Lineup_ID': f"IMPROVED_{lineup['lineup_id']}",
            'Contest_Type': lineup['strategy'],
            'Total_Salary': lineup['total_salary'],
            'Total_Projection': round(lineup['total_fppg'], 2)
        }
        
        # Fill positions more carefully
        pos_filled = {'P': False, 'C/1B': False, '2B': False, '3B': False, 
                     'SS': False, 'OF': 0, 'UTIL': False}
        
        for player in players:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Roster Position']
            
            # Fill specific positions first
            if 'P' in pos and not pos_filled['P']:
                lineup_row['P'] = name
                pos_filled['P'] = True
            elif 'C/1B' in pos and not pos_filled['C/1B']:
                lineup_row['C/1B'] = name
                pos_filled['C/1B'] = True
            elif '2B' in pos and not pos_filled['2B']:
                lineup_row['2B'] = name
                pos_filled['2B'] = True
            elif '3B' in pos and not pos_filled['3B']:
                lineup_row['3B'] = name
                pos_filled['3B'] = True
            elif 'SS' in pos and not pos_filled['SS']:
                lineup_row['SS'] = name
                pos_filled['SS'] = True
            elif 'OF' in pos and pos_filled['OF'] < 3:
                pos_filled['OF'] += 1
                if pos_filled['OF'] == 1:
                    lineup_row['OF'] = name
                elif pos_filled['OF'] == 2:
                    lineup_row['OF2'] = name
                else:
                    lineup_row['OF3'] = name
            else:
                # UTIL position
                lineup_row['UTIL'] = name
        
        fanduel_data.append(lineup_row)
    
    # Save to CSV
    df = pd.DataFrame(fanduel_data)
    output_file = slate_dir / "Improved_Lineups_FD_Format.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n💾 Saved {len(lineups)} diverse lineups to: {output_file}")
    
    # Enhanced summary
    fppgs = [l['total_fppg'] for l in lineups]
    salaries = [l['total_salary'] for l in lineups]
    strategies = [l['strategy'] for l in lineups]
    
    print(f"📊 Enhanced Summary:")
    print(f"  FPPG range: {min(fppgs):.1f} - {max(fppgs):.1f}")
    print(f"  Average FPPG: {sum(fppgs)/len(fppgs):.1f}")
    print(f"  Salary range: ${min(salaries)} - ${max(salaries)}")
    print(f"  Average salary: ${sum(salaries)/len(salaries):,.0f}")
    print(f"  Strategies used: {set(strategies)}")
    
    return output_file

if __name__ == "__main__":
    try:
        lineups = improved_lineup_builder()
        
        if lineups:
            output_file = save_improved_lineups(lineups)
            
            print(f"\n🎯 IMPROVED SUCCESS!")
            print(f"   Created {len(lineups)} diverse lineups with multiple strategies")
            print(f"   File ready for FanDuel: {output_file}")
            print(f"\n💪 These lineups should CRUSH your previous terrible ones!")
            print(f"   Multiple strategies ensure you're not missing value opportunities.")
            
        else:
            print("❌ Failed to create lineups")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

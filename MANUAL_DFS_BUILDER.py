#!/usr/bin/env python3
"""
ULTRA-SIMPLE DFS OPTIMIZER
==========================
Absolutely minimal optimizer that just works.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

def manual_lineup_builder():
    """Build lineups manually using simple logic"""
    
    print("STEP: ULTRA-SIMPLE DFS LINEUP BUILDER")
    print("=" * 50)
    
    # Load data
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    slate = pd.read_csv(slate_dir / "fd_slate_today.csv")
    
    # Clean data
    slate = slate[slate['FPPG'] > 2.0]  # Remove bad players
    slate = slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])
    
    print(f"Working with {len(slate)} clean players")
    
    # Calculate value
    slate['value'] = slate['FPPG'] / (slate['Salary'] / 1000)
    
    lineups = []
    
    for lineup_num in range(20):
        print(f"Building lineup {lineup_num + 1}...")
        
        # Simple greedy selection by value
        selected_players = []
        remaining_budget = 35000
        
        # Fill each position by best value within budget
        
        # 1. Pitcher
        pitchers = slate[slate['Roster Position'] == 'P']
        affordable_p = pitchers[pitchers['Salary'] <= remaining_budget]
        if not affordable_p.empty:
            # Mix of strategies
            if lineup_num < 5:  # First 5: highest value
                chosen = affordable_p.nlargest(1, 'value').iloc[0]
            elif lineup_num < 10:  # Next 5: balanced
                chosen = affordable_p.nlargest(10, 'value').sample(1).iloc[0]
            else:  # Last 10: more variety
                chosen = affordable_p.sample(1).iloc[0]
            
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]  # Remove from pool
        
        # 2. C/1B
        c1b = slate[slate['Roster Position'].str.contains('C/1B')]
        affordable_c1b = c1b[c1b['Salary'] <= remaining_budget]
        if not affordable_c1b.empty:
            chosen = affordable_c1b.nlargest(1, 'value').iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]
        
        # 3. 2B
        second_base = slate[slate['Roster Position'].str.contains('2B')]
        affordable_2b = second_base[second_base['Salary'] <= remaining_budget]
        if not affordable_2b.empty:
            chosen = affordable_2b.nlargest(1, 'value').iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]
        
        # 4. 3B
        third_base = slate[slate['Roster Position'].str.contains('3B')]
        affordable_3b = third_base[third_base['Salary'] <= remaining_budget]
        if not affordable_3b.empty:
            chosen = affordable_3b.nlargest(1, 'value').iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]
        
        # 5. SS
        shortstop = slate[slate['Roster Position'].str.contains('SS')]
        affordable_ss = shortstop[shortstop['Salary'] <= remaining_budget]
        if not affordable_ss.empty:
            chosen = affordable_ss.nlargest(1, 'value').iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]
        
        # 6-8. OF (3 players)
        for of_num in range(3):
            outfield = slate[slate['Roster Position'].str.contains('OF')]
            affordable_of = outfield[outfield['Salary'] <= remaining_budget]
            if not affordable_of.empty:
                chosen = affordable_of.nlargest(1, 'value').iloc[0]
                selected_players.append(chosen)
                remaining_budget -= chosen['Salary']
                slate = slate[slate['Id'] != chosen['Id']]
        
        # 9. UTIL (anyone eligible)
        util_eligible = slate[slate['Roster Position'].str.contains('UTIL')]
        affordable_util = util_eligible[util_eligible['Salary'] <= remaining_budget]
        if not affordable_util.empty:
            chosen = affordable_util.nlargest(1, 'value').iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            slate = slate[slate['Id'] != chosen['Id']]
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_fppg = sum(p['FPPG'] for p in selected_players)
            
            lineups.append({
                'players': selected_players,
                'total_salary': total_salary,
                'total_fppg': total_fppg,
                'lineup_id': lineup_num + 1
            })
            
            print(f"  SUCCESS: Salary: ${total_salary}, FPPG: {total_fppg:.1f}")
        else:
            print(f"  ERROR: Only got {len(selected_players)} players")
        
        # Reset slate for next lineup (reload fresh data)
        slate = pd.read_csv(slate_dir / "fd_slate_today.csv")
        slate = slate[slate['FPPG'] > 2.0]
        slate = slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])
        slate['value'] = slate['FPPG'] / (slate['Salary'] / 1000)
    
    return lineups

def save_manual_lineups(lineups):
    """Save lineups to FanDuel format"""
    if not lineups:
        print("No lineups to save!")
        return None
    
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    fanduel_data = []
    
    for lineup in lineups:
        players = lineup['players']
        
        # Create lineup row
        lineup_row = {
            'Lineup_ID': f"MANUAL_{lineup['lineup_id']}",
            'Contest_Type': 'manual',
            'Total_Salary': lineup['total_salary'],
            'Total_Projection': round(lineup['total_fppg'], 2)
        }
        
        # Fill positions
        for player in players:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Roster Position']
            
            if pos == 'P':
                lineup_row['P'] = name
            elif 'C/1B' in pos and 'C/1B' not in lineup_row:
                lineup_row['C/1B'] = name
            elif '2B' in pos and '2B' not in lineup_row:
                lineup_row['2B'] = name
            elif '3B' in pos and '3B' not in lineup_row:
                lineup_row['3B'] = name
            elif 'SS' in pos and 'SS' not in lineup_row:
                lineup_row['SS'] = name
            elif 'OF' in pos and 'OF' not in lineup_row:
                lineup_row['OF'] = name
            elif 'OF' in pos and 'OF2' not in lineup_row:
                lineup_row['OF2'] = name
            elif 'OF' in pos and 'OF3' not in lineup_row:
                lineup_row['OF3'] = name
            else:
                lineup_row['UTIL'] = name
        
        fanduel_data.append(lineup_row)
    
    # Save to CSV
    df = pd.DataFrame(fanduel_data)
    output_file = slate_dir / "Manual_Lineups_FD_Format.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n Saved {len(lineups)} lineups to: {output_file}")
    
    # Print summary
    fppgs = [l['total_fppg'] for l in lineups]
    salaries = [l['total_salary'] for l in lineups]
    
    print(f"DATA: Summary:")
    print(f"  FPPG range: {min(fppgs):.1f} - {max(fppgs):.1f}")
    print(f"  Average FPPG: {sum(fppgs)/len(fppgs):.1f}")
    print(f"  Salary range: ${min(salaries)} - ${max(salaries)}")
    print(f"  Average salary: ${sum(salaries)/len(salaries):,.0f}")
    
    return output_file

if __name__ == "__main__":
    try:
        lineups = manual_lineup_builder()
        
        if lineups:
            output_file = save_manual_lineups(lineups)
            
            print(f"\nCOMPLETE: SUCCESS!")
            print(f"   Created {len(lineups)} working lineups")
            print(f"   File ready for FanDuel: {output_file}")
            print(f"\nTIP: These manual lineups should perform much better!")
            print(f"   They use proper value-based selection instead of")
            print(f"   the broken optimization that was creating bad lineups.")
            
        else:
            print("ERROR: Failed to create lineups")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

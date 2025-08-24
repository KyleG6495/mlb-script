#!/usr/bin/env python3
"""
fix_lineup_generation.py
Fixes lineup generation by updating to current slate and improving projections
"""

import pandas as pd
import os
import glob
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_to_current_slate():
    """Update slate data to current confirmed starters"""
    print("🔄 UPDATING TO CURRENT SLATE")
    print("=" * 50)
    
    # Check if we have today's confirmed starters
    confirmed_file = "../data/fd_slate_confirmed_starters_only.csv"
    if not os.path.exists(confirmed_file):
        print("❌ No confirmed starters file found")
        print("   Need to run data pipeline first: 1_DATA_PIPELINE.bat")
        return False
    
    # Load confirmed starters
    confirmed_df = pd.read_csv(confirmed_file)
    print(f"✅ Found {len(confirmed_df)} confirmed starters for today")
    
    # Copy to fd_slate_today.csv for lineup generation
    today_slate_file = "../data/fd_slate_today.csv"
    confirmed_df.to_csv(today_slate_file, index=False)
    print(f"✅ Updated today's slate: {today_slate_file}")
    
    return True

def create_conservative_projections():
    """Create conservative projections based on historical averages"""
    print("\n🎯 CREATING CONSERVATIVE PROJECTIONS")
    print("=" * 50)
    
    slate_file = "../data/fd_slate_today.csv"
    if not os.path.exists(slate_file):
        print("❌ No slate file found")
        return False
    
    slate_df = pd.read_csv(slate_file)
    
    # Conservative FPPG estimates by position
    conservative_fppg = {
        'P': {'min': 15, 'avg': 25, 'max': 40},
        'C': {'min': 6, 'avg': 10, 'max': 18},
        '1B': {'min': 8, 'avg': 12, 'max': 20},
        '2B': {'min': 7, 'avg': 11, 'max': 18},
        '3B': {'min': 8, 'avg': 12, 'max': 20},
        'SS': {'min': 7, 'avg': 11, 'max': 18},
        'OF': {'min': 7, 'avg': 11, 'max': 18}
    }
    
    # Apply conservative projections
    def get_conservative_projection(row):
        position = row['Position']
        salary = row['Salary']
        
        # Map position
        if position in ['C', '1B', '2B', '3B', 'SS']:
            pos_key = position
        elif position in ['OF', 'LF', 'CF', 'RF']:
            pos_key = 'OF'
        elif position == 'P':
            pos_key = 'P'
        else:
            pos_key = 'OF'  # Default
        
        # Base projection on salary tier
        if salary >= 10000:  # Elite tier
            return conservative_fppg[pos_key]['max'] * 0.9  # 90% of max
        elif salary >= 7000:  # Mid tier
            return conservative_fppg[pos_key]['avg']
        else:  # Value tier
            return conservative_fppg[pos_key]['min'] * 1.2  # 120% of min
    
    slate_df['Conservative_FPPG'] = slate_df.apply(get_conservative_projection, axis=1)
    
    # Save updated slate with conservative projections
    conservative_slate_file = "../data/fd_slate_conservative_projections.csv"
    slate_df.to_csv(conservative_slate_file, index=False)
    
    print(f"✅ Created conservative projections: {conservative_slate_file}")
    
    # Show sample projections
    print("\n📊 SAMPLE CONSERVATIVE PROJECTIONS:")
    sample = slate_df.nlargest(10, 'Salary')[['First Name', 'Last Name', 'Position', 'Salary', 'Conservative_FPPG']]
    for _, row in sample.iterrows():
        print(f"   {row['First Name']} {row['Last Name']:15} {row['Position']:2} ${row['Salary']:5,} → {row['Conservative_FPPG']:5.1f} FPPG")
    
    return True

def create_diversified_lineup_generator():
    """Create a simple diversified lineup generator"""
    print("\n🎲 CREATING DIVERSIFIED LINEUP GENERATOR")
    print("=" * 50)
    
    script_content = '''#!/usr/bin/env python3
"""
conservative_lineup_generator.py
Generates diversified lineups using conservative projections
"""

import pandas as pd
import numpy as np
from itertools import combinations
import random

def generate_conservative_lineups(num_lineups=10):
    """Generate diversified lineups with conservative projections"""
    
    # Load slate with conservative projections
    slate_file = "../data/fd_slate_conservative_projections.csv"
    df = pd.read_csv(slate_file)
    
    print(f"Generating {num_lineups} conservative lineups...")
    
    lineups = []
    
    for i in range(num_lineups):
        lineup = generate_single_lineup(df, i)
        if lineup:
            lineups.append(lineup)
    
    return lineups

def generate_single_lineup(df, lineup_id):
    """Generate a single lineup with salary constraints"""
    
    # Position requirements for FanDuel
    positions_needed = {
        'P': 1,
        'C': 1, 
        '1B': 1,
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3
    }
    
    lineup_players = []
    total_salary = 0
    total_fppg = 0
    salary_cap = 35000
    
    # Select players by position with some randomization
    for pos, count in positions_needed.items():
        if pos == 'OF':
            # Handle outfielders specially
            of_players = df[df['Position'].isin(['OF', 'LF', 'CF', 'RF'])].copy()
        else:
            of_players = df[df['Position'] == pos].copy()
        
        if len(of_players) == 0:
            continue
            
        # Add some randomization based on lineup_id
        random.seed(42 + lineup_id * 7)  # Deterministic but different per lineup
        
        # Select top players with some variation
        if count == 1:
            # Single position - pick from top tier with randomization
            top_players = of_players.nlargest(min(5, len(of_players)), 'Conservative_FPPG')
            selected = top_players.sample(1).iloc[0]
            
            lineup_players.append({
                'player_name': f"{selected['First Name']} {selected['Last Name']}",
                'position': selected['Position'],
                'salary': selected['Salary'],
                'projected_fppg': selected['Conservative_FPPG'],
                'team': selected.get('Team', 'UNK')
            })
            
            total_salary += selected['Salary']
            total_fppg += selected['Conservative_FPPG']
        
        else:
            # Multiple positions (OF) - diversify
            top_players = of_players.nlargest(min(8, len(of_players)), 'Conservative_FPPG')
            selected_players = top_players.sample(min(count, len(top_players)))
            
            for _, selected in selected_players.iterrows():
                lineup_players.append({
                    'player_name': f"{selected['First Name']} {selected['Last Name']}",
                    'position': selected['Position'],
                    'salary': selected['Salary'],
                    'projected_fppg': selected['Conservative_FPPG'],
                    'team': selected.get('Team', 'UNK')
                })
                
                total_salary += selected['Salary']
                total_fppg += selected['Conservative_FPPG']
    
    # Validate lineup
    if len(lineup_players) == 9 and total_salary <= salary_cap:
        return {
            'lineup_id': f'lineup_{lineup_id + 1}',
            'players': lineup_players,
            'total_salary': total_salary,
            'projected_fppg': total_fppg
        }
    
    return None

def save_lineups(lineups):
    """Save lineups in the expected format"""
    
    # Create lineup details
    details_data = []
    summary_data = []
    
    for lineup in lineups:
        lineup_id = lineup['lineup_id']
        
        for player in lineup['players']:
            details_data.append({
                'lineup_id': lineup_id,
                'player_name': player['player_name'],
                'position': player['position'],
                'team': player['team'],
                'salary': player['salary'],
                'projected_fppg': player['projected_fppg'],
                'ownership': 15.0  # Default ownership estimate
            })
        
        summary_data.append({
            'lineup_id': lineup_id,
            'projected_fppg': lineup['projected_fppg'],
            'total_salary': lineup['total_salary']
        })
    
    # Save files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    details_df = pd.DataFrame(details_data)
    details_file = f"../data/conservative_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"../data/conservative_lineup_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    
    print(f"✅ Saved lineup details: {details_file}")
    print(f"✅ Saved lineup summary: {summary_file}")
    
    return details_file, summary_file

if __name__ == "__main__":
    from datetime import datetime
    import pandas as pd
    
    lineups = generate_conservative_lineups(10)
    
    if lineups:
        print(f"\\n🏆 GENERATED {len(lineups)} CONSERVATIVE LINEUPS")
        print("=" * 50)
        
        for lineup in lineups:
            print(f"{lineup['lineup_id']}: ${lineup['total_salary']:,} salary, {lineup['projected_fppg']:.1f} FPPG")
        
        save_lineups(lineups)
    else:
        print("❌ Failed to generate lineups")
'''
    
    # Save the generator script
    generator_file = "conservative_lineup_generator.py"
    with open(generator_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Created conservative lineup generator: {generator_file}")
    return True

def main():
    """Main function to fix lineup generation"""
    print("🔧 FIXING LINEUP GENERATION SYSTEM")
    print("=" * 60)
    
    # Step 1: Update to current slate
    if not update_to_current_slate():
        return
    
    # Step 2: Create conservative projections
    if not create_conservative_projections():
        return
    
    # Step 3: Create diversified lineup generator
    if not create_diversified_lineup_generator():
        return
    
    print("\n✅ LINEUP GENERATION FIXES COMPLETE!")
    print("=" * 60)
    print("🎯 NEXT STEPS:")
    print("   1. Run: python conservative_lineup_generator.py")
    print("   2. Test with: 3_BACKTEST_ANALYSIS.bat")
    print("   3. Compare accuracy vs old system")
    print("\n🔧 IMPROVEMENTS MADE:")
    print("   ✅ Updated to current confirmed starters slate")
    print("   ✅ Created conservative FPPG projections")
    print("   ✅ Built diversified lineup generator")
    print("   ✅ Added proper salary cap validation")

if __name__ == "__main__":
    main()

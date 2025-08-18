"""
Convert Enhanced DFS Lineups to FanDuel Submission Format
========================================================
"""

import pandas as pd
from datetime import datetime

def convert_lineups_to_fanduel_format():
    """Convert enhanced lineups to FanDuel submission format"""
    
    # Load today's enhanced lineups
    today_str = datetime.now().strftime('%Y%m%d')
    input_file = rf'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\enhanced_lineups_today_{today_str}.csv'
    
    try:
        df = pd.read_csv(input_file)
        print(f"SUCCESS: Loaded enhanced lineups: {input_file}")
        print(f"DATA: Found {len(df)} player entries across {df['lineup_id'].nunique()} lineups")
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_file}")
        print("SWAP: Make sure you've run the enhanced DFS optimizer first!")
        return
    
    # Get unique lineups
    lineup_ids = sorted(df['lineup_id'].unique())
    
    # Convert each lineup to FanDuel format
    all_fanduel_lineups = []
    
    for lineup_id in lineup_ids:
        lineup_df = df[df['lineup_id'] == lineup_id].sort_values('slot')
        
        # Create FanDuel format row
        fanduel_lineup = {}
        
        for idx, player in lineup_df.iterrows():
            slot = player['slot']
            
            # Map to FanDuel column names
            fanduel_lineup[f'P{slot}'] = player['name']
            fanduel_lineup[f'P{slot} ID'] = f"fd-{player['name'].replace(' ', '-').lower()}"
            fanduel_lineup[f'P{slot} Position'] = player['position']
            fanduel_lineup[f'P{slot} Salary'] = player['salary']
            fanduel_lineup[f'P{slot} Team'] = player['team']
            fanduel_lineup[f'P{slot} FPPG'] = round(player['enhanced_fppg'], 2)
        
        # Add lineup metadata
        fanduel_lineup['Lineup'] = f"Enhanced_{lineup_id}_{lineup_df.iloc[0]['strategy']}"
        fanduel_lineup['Total Salary'] = lineup_df['salary'].sum()
        fanduel_lineup['Projected FPPG'] = round(lineup_df['enhanced_fppg'].sum(), 1)
        fanduel_lineup['Strategy'] = lineup_df.iloc[0]['strategy']
        
        all_fanduel_lineups.append(fanduel_lineup)
    
    # Create DataFrame and save
    fanduel_df = pd.DataFrame(all_fanduel_lineups)
    
    # Save submission-ready file
    output_file = rf'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups_Ready_To_Submit_{today_str}.csv'
    fanduel_df.to_csv(output_file, index=False)
    
    print(f"\n FanDuel submission file created: {output_file}")
    print(f"DATA: Contains {len(fanduel_df)} optimized lineups")
    
    # Show top 3 lineups summary
    print(f"\nLINEUP: TOP 3 LINEUPS SUMMARY:")
    print("-" * 50)
    
    for i, lineup in fanduel_df.head(3).iterrows():
        print(f"\n#{i+1} - {lineup['Lineup']}")
        print(f"   Strategy: {lineup['Strategy']} | Salary: ${lineup['Total Salary']:,} | Projected: {lineup['Projected FPPG']} FPPG")
        
        # Show players
        for slot in range(1, 10):
            player_col = f'P{slot}'
            pos_col = f'P{slot} Position'
            salary_col = f'P{slot} Salary'
            fppg_col = f'P{slot} FPPG'
            
            if player_col in lineup:
                print(f"     {lineup[player_col]:<20} {lineup[pos_col]:<3} ${lineup[salary_col]:,} ({lineup[fppg_col]} FPPG)")
    
    print(f"\nSUCCESS: READY FOR FANDUEL SUBMISSION!")
    print(f" Upload this file to FanDuel: {output_file}")
    
    return output_file

if __name__ == "__main__":
    convert_lineups_to_fanduel_format()

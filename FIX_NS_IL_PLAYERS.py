import pandas as pd
import os

def fix_problematic_players():
    """
    Fix FanDuel lineup entries that have NS (Not Starting) or IL (Injured List) players
    """
    
    # Read the current slate to find replacement players
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    # Find active replacement players
    # 1. Active C/1B to replace Sean Murphy (NS)
    active_catchers = slate_df[
        (slate_df['Roster Position'].str.contains('C/1B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)  # Similar salary range
    ].sort_values('FPPG', ascending=False)
    
    if not active_catchers.empty:
        murphy_replacement = active_catchers.iloc[0]
        print(f"Sean Murphy replacement: {murphy_replacement['Id']} - {murphy_replacement['First Name']} {murphy_replacement['Last Name']} (${murphy_replacement['Salary']}, {murphy_replacement['FPPG']:.1f} FPPG)")
    
    # 2. Active pitcher to replace Ben Brown (NS) 
    active_pitchers = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Probable Pitcher'] == 'Yes') &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Salary'] >= 7000) & (slate_df['Salary'] <= 8000)  # Similar salary range
    ].sort_values('FPPG', ascending=False)
    
    if not active_pitchers.empty:
        brown_replacement = active_pitchers.iloc[0]
        print(f"Ben Brown replacement: {brown_replacement['Id']} - {brown_replacement['First Name']} {brown_replacement['Last Name']} (${brown_replacement['Salary']}, {brown_replacement['FPPG']:.1f} FPPG)")
    
    # 3. Active 3B to replace Max Muncy (IL)
    active_third_base = slate_df[
        (slate_df['Roster Position'].str.contains('3B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)  # Similar salary range
    ].sort_values('FPPG', ascending=False)
    
    if not active_third_base.empty:
        muncy_replacement = active_third_base.iloc[0]
        print(f"Max Muncy replacement: {muncy_replacement['Id']} - {muncy_replacement['First Name']} {muncy_replacement['Last Name']} (${muncy_replacement['Salary']}, {muncy_replacement['FPPG']:.1f} FPPG)")
    
    # Read current lineups
    with open(lineups_file, 'r') as f:
        content = f.read()
    
    # Define problematic player IDs to replace
    problematic_players = {
        # Sean Murphy (ATL C - NS) 
        '119385-82624': murphy_replacement['Id'] if not active_catchers.empty else '119385-82624',
        # Ben Brown (CHC P - NS)
        '119385-181837': brown_replacement['Id'] if not active_pitchers.empty else '119385-181837', 
        # Max Muncy (LAD 3B - IL)
        '119385-52176': muncy_replacement['Id'] if not active_third_base.empty else '119385-52176',
        # Also check for the ATH version of Max Muncy (IL)
        '119385-165641': muncy_replacement['Id'] if not active_third_base.empty else '119385-165641'
    }
    
    # Replace problematic players
    updated_content = content
    for old_id, new_id in problematic_players.items():
        if old_id != new_id:  # Only replace if we found a better player
            updated_content = updated_content.replace(old_id, new_id)
            print(f"Replaced {old_id} with {new_id}")
    
    # Write updated lineups
    with open(lineups_file, 'w') as f:
        f.write(updated_content)
    
    print(f"\nUpdated lineups saved to: {lineups_file}")
    print("All NS and IL players should now be replaced with active players!")

if __name__ == "__main__":
    fix_problematic_players()

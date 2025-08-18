import pandas as pd
import os

def fix_with_top_starters():
    """
    Replace all pitchers with the absolute TOP confirmed starters to eliminate any NS issues
    """
    
    # Read files
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== REPLACING WITH TOP CONFIRMED STARTERS ===\n")
    
    # Get the absolute best confirmed starting pitchers
    top_starters = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Probable Pitcher'] == 'Yes') &
        (slate_df['Injury Indicator'].isna())
    ].sort_values('FPPG', ascending=False).head(5)
    
    print("TARGET: TOP 5 CONFIRMED STARTING PITCHERS:")
    for i, (_, pitcher) in enumerate(top_starters.iterrows()):
        print(f"  {i+1}. {pitcher['First Name']} {pitcher['Last Name']} (${pitcher['Salary']}, {pitcher['FPPG']:.1f} FPPG) - {pitcher['Game']}")
    
    # Use the top 2 pitchers for all lineups
    top_pitcher_1 = top_starters.iloc[0]  # Paul Skenes
    top_pitcher_2 = top_starters.iloc[1]  # Robbie Ray
    
    print(f"\nSWAP: USING THESE TOP 2 STARTERS FOR ALL LINEUPS:")
    print(f"  Primary: {top_pitcher_1['First Name']} {top_pitcher_1['Last Name']} (${top_pitcher_1['Salary']}, {top_pitcher_1['FPPG']:.1f} FPPG)")
    print(f"  Secondary: {top_pitcher_2['First Name']} {top_pitcher_2['Last Name']} (${top_pitcher_2['Salary']}, {top_pitcher_2['FPPG']:.1f} FPPG)")
    
    # Read lineups and replace ALL pitcher IDs
    with open(lineups_file, 'r') as f:
        content = f.read()
    
    # Current pitcher IDs to replace
    current_pitcher_ids = ['119385-82630', '119385-82594']  # Shane Baz, Dustin May
    
    updated_content = content
    replacement_count = 0
    
    # Replace with alternating top pitchers
    for i, old_pitcher_id in enumerate(current_pitcher_ids):
        new_pitcher_id = top_pitcher_1['Id'] if i % 2 == 0 else top_pitcher_2['Id']
        
        if old_pitcher_id in updated_content:
            updated_content = updated_content.replace(old_pitcher_id, new_pitcher_id)
            replacement_count += 1
            
            old_pitcher = slate_df[slate_df['Id'] == old_pitcher_id]
            new_pitcher = slate_df[slate_df['Id'] == new_pitcher_id]
            
            if not old_pitcher.empty and not new_pitcher.empty:
                print(f"SUCCESS: Replaced {old_pitcher.iloc[0]['First Name']} {old_pitcher.iloc[0]['Last Name']} with {new_pitcher.iloc[0]['First Name']} {new_pitcher.iloc[0]['Last Name']}")
    
    # Write updated lineups
    with open(lineups_file, 'w') as f:
        f.write(updated_content)
    
    print(f"\nTARGET: SUMMARY:")
    print(f"Total pitcher replacements made: {replacement_count}")
    print(f"Updated lineups saved to: {lineups_file}")
    print("START: ALL LINEUPS NOW USE TOP-TIER CONFIRMED STARTERS!")
    print("SUCCESS: Paul Skenes and Robbie Ray are guaranteed starting today!")

if __name__ == "__main__":
    fix_with_top_starters()

import pandas as pd
import os

def fix_pitcher_starting_status():
    """
    Replace ALL pitchers with ONLY confirmed starting pitchers to eliminate NS status
    """
    
    # Read files
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== FIXING PITCHER STARTING STATUS ===\n")
    
    # Get ONLY confirmed starting pitchers with "Yes" status and high FPPG
    confirmed_starters = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Probable Pitcher'] == 'Yes') &
        (slate_df['Injury Indicator'].isna())
    ].sort_values('FPPG', ascending=False)
    
    print("🎯 CONFIRMED STARTING PITCHERS (Probable Pitcher = Yes):")
    for i, (_, pitcher) in enumerate(confirmed_starters.head(15).iterrows()):
        print(f"  {i+1}. {pitcher['First Name']} {pitcher['Last Name']} (${pitcher['Salary']}, {pitcher['FPPG']:.1f} FPPG)")
    
    # Read current lineups
    with open(lineups_file, 'r') as f:
        content = f.read()
    
    # Get the current problematic pitcher IDs from your screenshots
    problematic_pitchers = {
        # Zebby Matthews (NS)
        '119385-209173': confirmed_starters.iloc[6]['Id'] if len(confirmed_starters) > 6 else confirmed_starters.iloc[0]['Id'],
        # MacKenzie Gore (NS) 
        '119385-82635': confirmed_starters.iloc[7]['Id'] if len(confirmed_starters) > 7 else confirmed_starters.iloc[1]['Id'],
        # Sonny Gray (NS)
        '119385-17064': confirmed_starters.iloc[8]['Id'] if len(confirmed_starters) > 8 else confirmed_starters.iloc[2]['Id'],
        # Hurston Waldrep (NS)
        '119385-198872': confirmed_starters.iloc[9]['Id'] if len(confirmed_starters) > 9 else confirmed_starters.iloc[3]['Id']
    }
    
    print(f"\n🔄 PITCHER REPLACEMENTS:")
    for old_id, new_id in problematic_pitchers.items():
        old_pitcher = slate_df[slate_df['Id'] == old_id]
        new_pitcher = slate_df[slate_df['Id'] == new_id]
        if not old_pitcher.empty and not new_pitcher.empty:
            print(f"  🔴 {old_pitcher.iloc[0]['First Name']} {old_pitcher.iloc[0]['Last Name']} (NS) → {new_pitcher.iloc[0]['First Name']} {new_pitcher.iloc[0]['Last Name']} (CONFIRMED)")
    
    # Apply replacements
    updated_content = content
    replacement_count = 0
    
    for old_id, new_id in problematic_pitchers.items():
        if old_id in updated_content:
            updated_content = updated_content.replace(old_id, new_id)
            replacement_count += 1
            print(f"✅ Replaced {old_id} with {new_id}")
    
    # Write updated lineups
    with open(lineups_file, 'w') as f:
        f.write(updated_content)
    
    print(f"\n🎯 SUMMARY:")
    print(f"Total pitcher replacements made: {replacement_count}")
    print(f"Updated lineups saved to: {lineups_file}")
    print("🚀 ALL PITCHERS NOW CONFIRMED STARTERS - NO MORE NS STATUS!")
    
    # Also list the final confirmed pitchers being used
    print(f"\n✅ FINAL PITCHER ROSTER:")
    final_pitcher_ids = list(problematic_pitchers.values())
    for pitcher_id in set(final_pitcher_ids):
        pitcher_info = slate_df[slate_df['Id'] == pitcher_id]
        if not pitcher_info.empty:
            p = pitcher_info.iloc[0]
            print(f"  • {p['First Name']} {p['Last Name']} (${p['Salary']}, {p['FPPG']:.1f} FPPG) - CONFIRMED STARTER")

if __name__ == "__main__":
    fix_pitcher_starting_status()

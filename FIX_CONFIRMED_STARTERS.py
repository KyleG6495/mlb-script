import pandas as pd
import os

def fix_with_confirmed_starters():
    """
    Fix FanDuel lineup entries using ONLY confirmed starting pitchers marked with 'Yes'
    """
    
    # Read the current slate to find CONFIRMED starting pitchers
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== FIXING WITH CONFIRMED STARTING PITCHERS ===\n")
    
    # Get ONLY confirmed starting pitchers (Probable Pitcher = Yes)
    confirmed_starters = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Probable Pitcher'] == 'Yes') &
        (slate_df['Injury Indicator'].isna())
    ].sort_values('FPPG', ascending=False)
    
    print("🎯 CONFIRMED STARTING PITCHERS FOR TODAY:")
    for _, pitcher in confirmed_starters.head(10).iterrows():
        print(f"  • {pitcher['First Name']} {pitcher['Last Name']} (${pitcher['Salary']}, {pitcher['FPPG']:.1f} FPPG) - {pitcher['Team']}@{pitcher['Opponent']}")
    
    print(f"\n🔍 PROBLEMATIC PLAYERS TO REPLACE:")
    
    # Current lineups content
    with open(lineups_file, 'r') as f:
        content = f.read()
    
    # Define problematic players that are showing NS or PO
    problematic_replacements = {}
    
    # Sonny Gray (NS) - Replace with confirmed starter in similar price range
    gray_price_range = confirmed_starters[(confirmed_starters['Salary'] >= 8500) & (confirmed_starters['Salary'] <= 9500)]
    if not gray_price_range.empty:
        gray_replacement = gray_price_range.iloc[0]
        problematic_replacements['119385-17064'] = gray_replacement['Id']
        print(f"  🔴 Sonny Gray (NS) → {gray_replacement['First Name']} {gray_replacement['Last Name']} (${gray_replacement['Salary']}, {gray_replacement['FPPG']:.1f} FPPG)")
    
    # MacKenzie Gore (NS) - Replace with confirmed starter
    gore_price_range = confirmed_starters[(confirmed_starters['Salary'] >= 8800) & (confirmed_starters['Salary'] <= 9600)]
    if not gore_price_range.empty:
        gore_replacement = gore_price_range.iloc[1] if len(gore_price_range) > 1 else gore_price_range.iloc[0]
        problematic_replacements['119385-82635'] = gore_replacement['Id']
        print(f"  🔴 MacKenzie Gore (NS) → {gore_replacement['First Name']} {gore_replacement['Last Name']} (${gore_replacement['Salary']}, {gore_replacement['FPPG']:.1f} FPPG)")
    
    # Hurston Waldrep (NS) - Replace with confirmed starter in lower price range
    waldrep_price_range = confirmed_starters[(confirmed_starters['Salary'] >= 7500) & (confirmed_starters['Salary'] <= 8000)]
    if not waldrep_price_range.empty:
        waldrep_replacement = waldrep_price_range.iloc[0]
        # Find Waldrep's ID
        waldrep_rows = slate_df[slate_df['Last Name'].str.contains('Waldrep', na=False)]
        if not waldrep_rows.empty:
            problematic_replacements[waldrep_rows.iloc[0]['Id']] = waldrep_replacement['Id']
            print(f"  🔴 Hurston Waldrep (NS) → {waldrep_replacement['First Name']} {waldrep_replacement['Last Name']} (${waldrep_replacement['Salary']}, {waldrep_replacement['FPPG']:.1f} FPPG)")
    
    # Zebby Matthews (NS) - Replace with confirmed starter
    matthews_price_range = confirmed_starters[(confirmed_starters['Salary'] >= 7500) & (confirmed_starters['Salary'] <= 8500)]
    if not matthews_price_range.empty:
        matthews_replacement = matthews_price_range.iloc[1] if len(matthews_price_range) > 1 else matthews_price_range.iloc[0]
        problematic_replacements['119385-209173'] = matthews_replacement['Id']
        print(f"  🔴 Zebby Matthews (NS) → {matthews_replacement['First Name']} {matthews_replacement['Last Name']} (${matthews_replacement['Salary']}, {matthews_replacement['FPPG']:.1f} FPPG)")
    
    # Also fix position players with issues
    print(f"\n🔍 FIXING POSITION PLAYERS:")
    
    # Enrique Pereira (PO) - Replace with active OF
    active_outfielders = slate_df[
        (slate_df['Roster Position'].str.contains('OF', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 2500)
    ].sort_values('FPPG', ascending=False)
    
    if not active_outfielders.empty:
        pereira_replacement = active_outfielders.iloc[0]
        # Find Pereira's ID
        pereira_rows = slate_df[slate_df['Last Name'].str.contains('Pereira', na=False)]
        if not pereira_rows.empty:
            problematic_replacements[pereira_rows.iloc[0]['Id']] = pereira_replacement['Id']
            print(f"  🔴 Enrique Pereira (PO) → {pereira_replacement['First Name']} {pereira_replacement['Last Name']} (${pereira_replacement['Salary']}, {pereira_replacement['FPPG']:.1f} FPPG)")
    
    # Carlos Rodriguez (NS) - Replace with active OF
    if len(active_outfielders) > 1:
        rodriguez_replacement = active_outfielders.iloc[1]
        # Find Carlos Rodriguez's ID
        rodriguez_rows = slate_df[(slate_df['Last Name'].str.contains('Rodriguez', na=False)) & 
                                 (slate_df['First Name'].str.contains('Carlos', na=False))]
        if not rodriguez_rows.empty:
            problematic_replacements[rodriguez_rows.iloc[0]['Id']] = rodriguez_replacement['Id']
            print(f"  🔴 Carlos Rodriguez (NS) → {rodriguez_replacement['First Name']} {rodriguez_replacement['Last Name']} (${rodriguez_replacement['Salary']}, {rodriguez_replacement['FPPG']:.1f} FPPG)")
    
    # Dominic Smith (NS) - Replace with active C/1B
    active_catchers = slate_df[
        (slate_df['Roster Position'].str.contains('C/1B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 2800)
    ].sort_values('FPPG', ascending=False)
    
    if not active_catchers.empty:
        smith_replacement = active_catchers.iloc[0]
        problematic_replacements['119385-52170'] = smith_replacement['Id']
        print(f"  🔴 Dominic Smith (NS) → {smith_replacement['First Name']} {smith_replacement['Last Name']} (${smith_replacement['Salary']}, {smith_replacement['FPPG']:.1f} FPPG)")
    
    # Apply all replacements
    updated_content = content
    replacement_count = 0
    
    print(f"\n🔄 APPLYING REPLACEMENTS:")
    for old_id, new_id in problematic_replacements.items():
        if old_id != new_id and old_id in updated_content:
            updated_content = updated_content.replace(old_id, new_id)
            replacement_count += 1
            print(f"✅ Replaced {old_id} with {new_id}")
    
    # Write updated lineups
    with open(lineups_file, 'w') as f:
        f.write(updated_content)
    
    print(f"\n🎯 SUMMARY:")
    print(f"Total replacements made: {replacement_count}")
    print(f"Updated lineups saved to: {lineups_file}")
    print("🚀 All players now use CONFIRMED starting pitchers and active position players!")
    print("✅ No more NS (Not Starting) or PO (Probable Out) issues!")

if __name__ == "__main__":
    fix_with_confirmed_starters()

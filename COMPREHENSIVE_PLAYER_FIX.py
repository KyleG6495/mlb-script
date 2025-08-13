import pandas as pd
import os

def fix_comprehensive_player_issues():
    """
    Fix FanDuel lineup entries with comprehensive player replacements for IL, NS, and PO status players
    """
    
    # Read the current slate to find replacement players
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== COMPREHENSIVE PLAYER REPLACEMENTS ===\n")
    
    # Define problematic players and find active replacements
    
    # 1. PITCHERS with issues
    print("🔴 PITCHER REPLACEMENTS:")
    
    # Shane Bieber (IL - Elbow) - Replace with active pitcher in similar price range
    active_pitchers_9k = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Salary'] >= 8900) & (slate_df['Salary'] <= 9300)
    ].sort_values('FPPG', ascending=False)
    
    bieber_replacement = active_pitchers_9k.iloc[0] if not active_pitchers_9k.empty else None
    print(f"Shane Bieber (IL-Elbow) → {bieber_replacement['First Name']} {bieber_replacement['Last Name']} (${bieber_replacement['Salary']}, {bieber_replacement['FPPG']:.1f} FPPG)")
    
    # Joe Ryan (NS) - Replace with active pitcher in similar price range
    ryan_replacement = active_pitchers_9k.iloc[1] if len(active_pitchers_9k) > 1 else bieber_replacement
    print(f"Joe Ryan (NS) → {ryan_replacement['First Name']} {ryan_replacement['Last Name']} (${ryan_replacement['Salary']}, {ryan_replacement['FPPG']:.1f} FPPG)")
    
    # Hayden Waldrep (NS) - Lower cost pitcher replacement
    active_pitchers_7k = slate_df[
        (slate_df['Position'] == 'P') &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Salary'] >= 7600) & (slate_df['Salary'] <= 8000)
    ].sort_values('FPPG', ascending=False)
    
    waldrep_replacement = active_pitchers_7k.iloc[0] if not active_pitchers_7k.empty else None
    print(f"Hayden Waldrep (NS) → {waldrep_replacement['First Name']} {waldrep_replacement['Last Name']} (${waldrep_replacement['Salary']}, {waldrep_replacement['FPPG']:.1f} FPPG)")
    
    # Chayce Bradford (IL) - Lower cost pitcher
    bradford_replacement = active_pitchers_7k.iloc[1] if len(active_pitchers_7k) > 1 else waldrep_replacement
    print(f"Chayce Bradford (IL) → {bradford_replacement['First Name']} {bradford_replacement['Last Name']} (${bradford_replacement['Salary']}, {bradford_replacement['FPPG']:.1f} FPPG)")
    
    # 2. POSITION PLAYERS with issues
    print(f"\n🔴 POSITION PLAYER REPLACEMENTS:")
    
    # Thairo Estrada (IL - Hamstring) - 2B replacement
    active_2b = slate_df[
        (slate_df['Roster Position'].str.contains('2B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)
    ].sort_values('FPPG', ascending=False)
    
    estrada_replacement = active_2b.iloc[0] if not active_2b.empty else None
    print(f"Thairo Estrada (IL-Hamstring) → {estrada_replacement['First Name']} {estrada_replacement['Last Name']} (${estrada_replacement['Salary']}, {estrada_replacement['FPPG']:.1f} FPPG)")
    
    # Yasmani Grandal (NS) - C/1B replacement
    active_catchers = slate_df[
        (slate_df['Roster Position'].str.contains('C/1B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 2500)
    ].sort_values('FPPG', ascending=False)
    
    grandal_replacement = active_catchers.iloc[0] if not active_catchers.empty else None
    print(f"Yasmani Grandal (NS) → {grandal_replacement['First Name']} {grandal_replacement['Last Name']} (${grandal_replacement['Salary']}, {grandal_replacement['FPPG']:.1f} FPPG)")
    
    # Miguel Amaya (NS) - C/1B replacement
    amaya_replacement = active_catchers.iloc[1] if len(active_catchers) > 1 else grandal_replacement
    print(f"Miguel Amaya (NS) → {amaya_replacement['First Name']} {amaya_replacement['Last Name']} (${amaya_replacement['Salary']}, {amaya_replacement['FPPG']:.1f} FPPG)")
    
    # Outfielders with issues
    active_outfielders = slate_df[
        (slate_df['Roster Position'].str.contains('OF', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)
    ].sort_values('FPPG', ascending=False)
    
    # Sam Hilliard (NS)
    hilliard_replacement = active_outfielders.iloc[0] if not active_outfielders.empty else None
    print(f"Sam Hilliard (NS) → {hilliard_replacement['First Name']} {hilliard_replacement['Last Name']} (${hilliard_replacement['Salary']}, {hilliard_replacement['FPPG']:.1f} FPPG)")
    
    # Carlos Rodriguez (NS)
    rodriguez_replacement = active_outfielders.iloc[1] if len(active_outfielders) > 1 else hilliard_replacement
    print(f"Carlos Rodriguez (NS) → {rodriguez_replacement['First Name']} {rodriguez_replacement['Last Name']} (${rodriguez_replacement['Salary']}, {rodriguez_replacement['FPPG']:.1f} FPPG)")
    
    # Matthew Lugo (NS)
    lugo_replacement = active_outfielders.iloc[2] if len(active_outfielders) > 2 else hilliard_replacement
    print(f"Matthew Lugo (NS) → {lugo_replacement['First Name']} {lugo_replacement['Last Name']} (${lugo_replacement['Salary']}, {lugo_replacement['FPPG']:.1f} FPPG)")
    
    # George Springer (IL)
    springer_replacement = active_outfielders.iloc[3] if len(active_outfielders) > 3 else hilliard_replacement
    print(f"George Springer (IL) → {springer_replacement['First Name']} {springer_replacement['Last Name']} (${springer_replacement['Salary']}, {springer_replacement['FPPG']:.1f} FPPG)")
    
    # Jake Burger (NS) - 3B/UTIL replacement
    active_third_base = slate_df[
        (slate_df['Roster Position'].str.contains('3B', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)
    ].sort_values('FPPG', ascending=False)
    
    burger_replacement = active_third_base.iloc[0] if not active_third_base.empty else None
    print(f"Jake Burger (NS) → {burger_replacement['First Name']} {burger_replacement['Last Name']} (${burger_replacement['Salary']}, {burger_replacement['FPPG']:.1f} FPPG)")
    
    # Read current lineups
    with open(lineups_file, 'r') as f:
        content = f.read()
    
    # Define all problematic player ID replacements
    player_replacements = {}
    
    # Add pitcher replacements if found
    if bieber_replacement is not None:
        player_replacements['119385-82554'] = bieber_replacement['Id']  # Shane Bieber
    if ryan_replacement is not None:
        player_replacements['119385-119430'] = ryan_replacement['Id']  # Joe Ryan
    if waldrep_replacement is not None:
        # Search for Waldrep's actual ID in slate
        waldrep_rows = slate_df[slate_df['Last Name'].str.contains('Waldrep', na=False)]
        if not waldrep_rows.empty:
            player_replacements[waldrep_rows.iloc[0]['Id']] = waldrep_replacement['Id']
    if bradford_replacement is not None:
        # Search for Bradford's actual ID in slate  
        bradford_rows = slate_df[slate_df['Last Name'].str.contains('Bradford', na=False)]
        if not bradford_rows.empty:
            player_replacements[bradford_rows.iloc[0]['Id']] = bradford_replacement['Id']
    
    # Add position player replacements if found
    if estrada_replacement is not None:
        player_replacements['119385-82613'] = estrada_replacement['Id']  # Thairo Estrada
    if grandal_replacement is not None:
        # Search for Grandal's actual ID
        grandal_rows = slate_df[slate_df['Last Name'].str.contains('Grandal', na=False)]
        if not grandal_rows.empty:
            player_replacements[grandal_rows.iloc[0]['Id']] = grandal_replacement['Id']
    if amaya_replacement is not None:
        # Search for Amaya's actual ID
        amaya_rows = slate_df[slate_df['Last Name'].str.contains('Amaya', na=False)]
        if not amaya_rows.empty:
            player_replacements[amaya_rows.iloc[0]['Id']] = amaya_replacement['Id']
    if hilliard_replacement is not None:
        # Search for Hilliard's actual ID
        hilliard_rows = slate_df[slate_df['Last Name'].str.contains('Hilliard', na=False)]
        if not hilliard_rows.empty:
            player_replacements[hilliard_rows.iloc[0]['Id']] = hilliard_replacement['Id']
    if rodriguez_replacement is not None:
        # Search for Carlos Rodriguez's actual ID
        rodriguez_rows = slate_df[(slate_df['Last Name'].str.contains('Rodriguez', na=False)) & 
                                 (slate_df['First Name'].str.contains('Carlos', na=False))]
        if not rodriguez_rows.empty:
            player_replacements[rodriguez_rows.iloc[0]['Id']] = rodriguez_replacement['Id']
    if lugo_replacement is not None:
        # Search for Matthew Lugo's actual ID
        lugo_rows = slate_df[(slate_df['Last Name'].str.contains('Lugo', na=False)) & 
                           (slate_df['First Name'].str.contains('Matthew', na=False))]
        if not lugo_rows.empty:
            player_replacements[lugo_rows.iloc[0]['Id']] = lugo_replacement['Id']
    if springer_replacement is not None:
        # Search for Springer's actual ID
        springer_rows = slate_df[slate_df['Last Name'].str.contains('Springer', na=False)]
        if not springer_rows.empty:
            player_replacements[springer_rows.iloc[0]['Id']] = springer_replacement['Id']
    if burger_replacement is not None:
        # Search for Burger's actual ID
        burger_rows = slate_df[slate_df['Last Name'].str.contains('Burger', na=False)]
        if not burger_rows.empty:
            player_replacements[burger_rows.iloc[0]['Id']] = burger_replacement['Id']
    
    # Apply replacements
    updated_content = content
    replacement_count = 0
    
    print(f"\n🔄 APPLYING REPLACEMENTS:")
    for old_id, new_id in player_replacements.items():
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
    print("🚀 All IL, NS, and PO players should now be replaced with active confirmed starters!")

if __name__ == "__main__":
    fix_comprehensive_player_issues()

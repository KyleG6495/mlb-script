import pandas as pd
import numpy as np

def fix_slate_filtering():
    """
    EMERGENCY FIX: Filter out IL players and non-probable pitchers
    """
    
    print("=== EMERGENCY SLATE FILTERING FIX ===")
    print("Removing IL players and non-probable pitchers...")
    
    # Load the corrected slate
    slate_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\CORRECTED_slate_20250813_072440.csv")
    
    print(f"Original slate: {len(slate_df)} players")
    
    # Show IL players before filtering
    il_players = slate_df[slate_df['Injury Indicator'] == 'IL']
    print(f"\n🚨 FOUND {len(il_players)} IL PLAYERS:")
    for _, player in il_players.iterrows():
        name = f"{player['First Name']} {player['Last Name']}"
        print(f"  - {name:20} ({player['Position']}) ${player['Salary']:,} - {player['Injury Details']}")
    
    # Show non-probable pitchers
    non_probable_pitchers = slate_df[(slate_df['Position'] == 'P') & (slate_df['Probable Pitcher'].isna())]
    print(f"\n🚨 FOUND {len(non_probable_pitchers)} NON-PROBABLE PITCHERS:")
    for _, player in non_probable_pitchers.iterrows():
        name = f"{player['First Name']} {player['Last Name']}"
        print(f"  - {name:20} ${player['Salary']:,}")
    
    # Filter out problematic players
    print("\n=== APPLYING FILTERS ===")
    
    # Remove IL players
    slate_df = slate_df[slate_df['Injury Indicator'] != 'IL']
    print(f"✅ Removed IL players: {len(slate_df)} players remaining")
    
    # Remove non-probable pitchers
    slate_df = slate_df[~((slate_df['Position'] == 'P') & (slate_df['Probable Pitcher'].isna()))]
    print(f"✅ Removed non-probable pitchers: {len(slate_df)} players remaining")
    
    # Remove players with 0 or negative projections
    slate_df = slate_df[slate_df['FPPG'] > 0]
    print(f"✅ Removed 0/negative projections: {len(slate_df)} players remaining")
    
    # Save filtered slate
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"c:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\FILTERED_CORRECTED_slate_{timestamp}.csv"
    slate_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved filtered slate: FILTERED_CORRECTED_slate_{timestamp}.csv")
    print(f"Final slate: {len(slate_df)} playable players")
    
    # Show top projected players after filtering
    print("\n=== TOP 10 PROJECTED PLAYERS (AFTER FILTERING) ===")
    top_players = slate_df.nlargest(10, 'FPPG')[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'Team', 'Probable Pitcher']]
    for _, player in top_players.iterrows():
        name = f"{player['First Name']} {player['Last Name']}"
        probable = "✅" if pd.notna(player['Probable Pitcher']) else "❌"
        print(f"{name:20} ({player['Position']:2}) ${player['Salary']:,} | {player['FPPG']:5.1f} | {player['Team']} | Probable: {probable}")
    
    return output_file

if __name__ == "__main__":
    filtered_file = fix_slate_filtering()

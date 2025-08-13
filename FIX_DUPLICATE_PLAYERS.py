import pandas as pd
import os

def fix_duplicate_players():
    """
    Fix FanDuel lineup entries that have the same player in multiple positions
    """
    
    # Read the current slate to find replacement players
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== FIXING DUPLICATE PLAYER ISSUES ===\n")
    
    # Read current lineups
    with open(lineups_file, 'r') as f:
        lines = f.readlines()
    
    # Find entries with duplicates and fix them
    fixed_lines = []
    
    for line in lines:
        if line.startswith('3552555021') or line.startswith('3552555027'):
            # These entries have 119385-181797 (Warming Bernabel) in both 3B and UTIL
            print(f"🔍 Analyzing entry: {line.split(',')[0]}")
            
            parts = line.strip().split(',')
            if len(parts) >= 10:
                # Check positions: P,C/1B,2B,3B,SS,OF,OF,OF,UTIL
                positions = parts[4:13]  # positions 4-12 are the player positions
                
                # Find the duplicate player (119385-181797)
                duplicate_player = '119385-181797'
                duplicate_positions = []
                
                for i, player_id in enumerate(positions):
                    if player_id == duplicate_player:
                        duplicate_positions.append(i)
                
                if len(duplicate_positions) > 1:
                    print(f"🔴 Found duplicate player {duplicate_player} in positions {duplicate_positions}")
                    
                    # Replace the UTIL position (last occurrence) with a different player
                    # Find a suitable UTIL replacement from active players
                    util_eligible = slate_df[
                        (slate_df['Roster Position'].str.contains('UTIL', na=False)) &
                        (slate_df['Injury Indicator'].isna()) &
                        (slate_df['Batting Order'].notna()) &
                        (slate_df['Salary'] <= 3500) &  # Similar price range
                        (~slate_df['Id'].isin(positions))  # Not already in lineup
                    ].sort_values('FPPG', ascending=False)
                    
                    if not util_eligible.empty:
                        replacement_player = util_eligible.iloc[0]
                        print(f"✅ Replacing UTIL position with: {replacement_player['First Name']} {replacement_player['Last Name']} (${replacement_player['Salary']}, {replacement_player['FPPG']:.1f} FPPG)")
                        
                        # Replace the last occurrence (UTIL position)
                        parts[duplicate_positions[-1] + 4] = replacement_player['Id']
                        
                        # Reconstruct the line
                        line = ','.join(parts) + '\n'
                    else:
                        print("❌ No suitable replacement found")
        
        fixed_lines.append(line)
    
    # Write the fixed lineups
    with open(lineups_file, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"\n🎯 SUMMARY:")
    print(f"Fixed duplicate player issues in entries 3552555021 and 3552555027")
    print(f"Updated lineups saved to: {lineups_file}")
    print("🚀 All duplicate player issues should now be resolved!")

if __name__ == "__main__":
    fix_duplicate_players()

import pandas as pd
import os

def fix_position_eligibility():
    """
    Fix position eligibility issues - replace Carson Kelly in OF positions with actual outfielders
    """
    
    # Read files
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    
    print("=== FIXING POSITION ELIGIBILITY ISSUES ===\n")
    
    # Find Carson Kelly's ID that's causing issues
    kelly_id = '119385-73871'
    print(f"🔴 PROBLEM: Carson Kelly ({kelly_id}) is a C/1B being used in OF positions")
    
    # Find suitable outfielders as replacements
    eligible_outfielders = slate_df[
        (slate_df['Roster Position'].str.contains('OF', na=False)) &
        (slate_df['Injury Indicator'].isna()) &
        (slate_df['Batting Order'].notna()) &
        (slate_df['Salary'] <= 3000)  # Similar price range
    ].sort_values('FPPG', ascending=False)
    
    print("🔍 AVAILABLE OUTFIELDER REPLACEMENTS:")
    for i, (_, player) in enumerate(eligible_outfielders.head(5).iterrows()):
        print(f"  {i+1}. {player['First Name']} {player['Last Name']} (${player['Salary']}, {player['FPPG']:.1f} FPPG) - {player['Roster Position']}")
    
    # Select top 3 outfielders for OF positions
    if len(eligible_outfielders) >= 3:
        of1_replacement = eligible_outfielders.iloc[0]
        of2_replacement = eligible_outfielders.iloc[1] 
        of3_replacement = eligible_outfielders.iloc[2]
        
        print(f"\n✅ REPLACEMENTS SELECTED:")
        print(f"  OF1: {of1_replacement['First Name']} {of1_replacement['Last Name']} (${of1_replacement['Salary']}, {of1_replacement['FPPG']:.1f} FPPG)")
        print(f"  OF2: {of2_replacement['First Name']} {of2_replacement['Last Name']} (${of2_replacement['Salary']}, {of2_replacement['FPPG']:.1f} FPPG)")
        print(f"  OF3: {of3_replacement['First Name']} {of3_replacement['Last Name']} (${of3_replacement['Salary']}, {of3_replacement['FPPG']:.1f} FPPG)")
        
        # Read and fix the lineups
        with open(lineups_file, 'r') as f:
            content = f.read()
        
        # Find entries that have Carson Kelly in OF positions and fix them
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.startswith(('3552555017', '3552555023', '3552555024', '3552555025', '3552555028', '3552555029')):
                parts = line.split(',')
                if len(parts) >= 12:
                    # Positions: P,C/1B,2B,3B,SS,OF,OF,OF,UTIL (indices 4-12)
                    # Replace Carson Kelly in OF positions (indices 9, 10, 11) with actual outfielders
                    if parts[9] == kelly_id:  # First OF position
                        parts[9] = of1_replacement['Id']
                    if parts[10] == kelly_id:  # Second OF position  
                        parts[10] = of2_replacement['Id']
                    if parts[11] == kelly_id:  # Third OF position
                        parts[11] = of3_replacement['Id']
                    
                    line = ','.join(parts)
            
            fixed_lines.append(line)
        
        # Write the fixed content
        with open(lineups_file, 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"\n🔄 APPLIED FIXES:")
        print(f"✅ Replaced Carson Kelly in OF positions with eligible outfielders")
        print(f"✅ All failed entries should now have valid position eligibility")
        print(f"✅ Updated lineups saved to: {lineups_file}")
        print(f"\n🚀 FanDuel should now accept all lineups without 'invalid roster' errors!")
        
    else:
        print("❌ Not enough eligible outfielders found for replacement")

if __name__ == "__main__":
    fix_position_eligibility()

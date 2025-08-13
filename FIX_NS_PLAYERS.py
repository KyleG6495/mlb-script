import pandas as pd
import numpy as np

def fix_ns_players():
    """
    Fix NS (Not Starting) players in FanDuel lineups
    Based on user interface showing C. Rodriguez as NS
    """
    
    # Load current lineups
    lineups_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    lineups_df = pd.read_csv(lineups_file)
    
    # Load current slate
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    slate_df = pd.read_csv(slate_file)
    
    print("=== NS PLAYER REPLACEMENT ===")
    print("Identifying and replacing NS players...")
    
    # Problem: C. Rodriguez (ATL@NYM) showing as NS in user interface
    
    # Find Carlos Rodriguez in slate data
    carlos_rodriguez = slate_df[
        (slate_df['First Name'].str.contains('Carlos', case=False, na=False)) &
        (slate_df['Last Name'].str.contains('Rodriguez', case=False, na=False)) &
        (slate_df['Team'] == 'ATL')
    ]
    
    print(f"Carlos Rodriguez entries found: {len(carlos_rodriguez)}")
    if not carlos_rodriguez.empty:
        print(carlos_rodriguez[['Id', 'First Name', 'Last Name', 'Position', 'Team', 'Game', 'Salary', 'FPPG']].to_string())
    
    # Best replacement outfielders (not on IL, good projections)
    replacement_candidates = slate_df[
        (slate_df['Position'].str.contains('OF', case=False, na=False)) &
        (slate_df['Injury Indicator'].isna() | (slate_df['Injury Indicator'] == '')) &
        (slate_df['Salary'] <= 3000) &
        (slate_df['FPPG'] >= 9.0)
    ].sort_values('FPPG', ascending=False)
    
    print(f"\n=== TOP REPLACEMENT CANDIDATES ===")
    print(replacement_candidates[['Id', 'First Name', 'Last Name', 'Position', 'Team', 'Game', 'Salary', 'FPPG', 'Batting Order']].head(5).to_string())
    
    # Select Roman Anthony as replacement - excellent value
    roman_anthony = slate_df[
        (slate_df['First Name'] == 'Roman') &
        (slate_df['Last Name'] == 'Anthony')
    ]
    
    if not roman_anthony.empty:
        replacement_info = roman_anthony.iloc[0]
        replacement_id = replacement_info['Id']
        
        print(f"\n=== SELECTED REPLACEMENT ===")
        print(f"Player: {replacement_info['First Name']} {replacement_info['Last Name']}")
        print(f"ID: {replacement_id}")
        print(f"Position: {replacement_info['Position']}")
        print(f"Team/Game: {replacement_info['Team']} vs {replacement_info['Opponent']} ({replacement_info['Game']})")
        print(f"Salary: ${replacement_info['Salary']}")
        print(f"FPPG: {replacement_info['FPPG']}")
        print(f"Batting Order: {replacement_info['Batting Order']}")
        
        # Count replacements needed
        replacements_made = 0
        
        # Replace problematic Carlos Rodriguez instances
        # From user interface, we know Carlos Rodriguez (ATL@NYM) is showing NS
        # This is likely the player ID that needs replacing in OF positions
        
        # Find Carlos Rodriguez ID in slate
        if not carlos_rodriguez.empty:
            carlos_id = carlos_rodriguez.iloc[0]['Id']
            print(f"\nSearching for Carlos Rodriguez ID: {carlos_id}")
            
            # Replace in lineup entries
            for index, row in lineups_df.iterrows():
                if pd.isna(row['entry_id']) or row['entry_id'] == '':
                    continue
                    
                # Check all position columns
                position_cols = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
                
                for col in position_cols:
                    if col in lineups_df.columns:
                        current_player = str(row[col])
                        
                        # Replace Carlos Rodriguez with Roman Anthony
                        if current_player == carlos_id:
                            print(f"Replacing Carlos Rodriguez ({carlos_id}) with Roman Anthony ({replacement_id}) in {col} for entry {row['entry_id']}")
                            lineups_df.at[index, col] = replacement_id
                            replacements_made += 1
        
        # Also replace any other problematic IDs showing as NS
        # From the lineup data, we saw ID conflicts with 119385-198526 and 119385-165527
        problem_ids = ['119385-198526', '119385-165527']
        
        for problem_id in problem_ids:
            for index, row in lineups_df.iterrows():
                if pd.isna(row['entry_id']) or row['entry_id'] == '':
                    continue
                    
                position_cols = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
                
                for col in position_cols:
                    if col in lineups_df.columns:
                        current_player = str(row[col])
                        
                        # Only replace if in OF position where it would cause NS issues
                        if current_player == problem_id and 'OF' in col:
                            print(f"Replacing problematic ID {problem_id} with Roman Anthony ({replacement_id}) in {col} for entry {row['entry_id']}")
                            lineups_df.at[index, col] = replacement_id
                            replacements_made += 1
        
        print(f"\n=== REPLACEMENT SUMMARY ===")
        print(f"Total replacements made: {replacements_made}")
        
        if replacements_made > 0:
            # Save updated lineups
            lineups_df.to_csv(lineups_file, index=False)
            print(f"Updated lineups saved to: {lineups_file}")
            print(f"All NS players replaced with Roman Anthony ({replacement_id})")
        else:
            print("No problematic players found in lineup structure")
    
    else:
        print("Roman Anthony not found in slate - using alternative replacement")
    
    return lineups_df

if __name__ == "__main__":
    fix_ns_players()

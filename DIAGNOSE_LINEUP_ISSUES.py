import pandas as pd
import os

def diagnose_lineup_issues():
    """
    Diagnose what's causing 'Please supply a valid roster' errors in FanDuel lineups
    """
    
    # Read files
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    lineups_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
    
    slate_df = pd.read_csv(slate_file)
    lineups_df = pd.read_csv(lineups_file)
    
    print("=== DIAGNOSING FANDUEL LINEUP ISSUES ===\n")
    
    # Failed entries
    failed_entries = ['3552555023', '3552555017', '3552555029', '3552555028', '3552555025', '3552555024']
    
    for entry_id in failed_entries:
        print(f" ANALYZING ENTRY {entry_id}:")
        
        # Get the lineup
        lineup_row = lineups_df[lineups_df['entry_id'] == int(entry_id)]
        if lineup_row.empty:
            print(f"  ERROR: Entry not found")
            continue
            
        lineup = lineup_row.iloc[0]
        
        # Check each position
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
        player_ids = [lineup['P'], lineup['C/1B'], lineup['2B'], lineup['3B'], lineup['SS'], 
                     lineup['OF'], lineup['OF'], lineup['OF'], lineup['UTIL']]
        
        total_salary = 0
        position_violations = []
        missing_players = []
        
        for i, (pos, player_id) in enumerate(zip(positions, player_ids)):
            if pd.isna(player_id):
                missing_players.append(pos)
                continue
                
            # Find player in slate
            player_info = slate_df[slate_df['Id'] == player_id]
            if player_info.empty:
                missing_players.append(f"{pos}: {player_id}")
                continue
                
            player = player_info.iloc[0]
            total_salary += player['Salary']
            
            # Check position eligibility
            eligible_positions = str(player['Roster Position']).split('/')
            
            # Map FanDuel positions to roster positions
            pos_mapping = {
                'P': ['P'],
                'C/1B': ['C', '1B', 'C/1B'],
                '2B': ['2B'],
                '3B': ['3B'],
                'SS': ['SS'],
                'OF': ['OF'],
                'UTIL': ['C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']
            }
            
            if pos in pos_mapping:
                valid_for_position = any(ep.strip() in pos_mapping[pos] for ep in eligible_positions)
                if not valid_for_position:
                    position_violations.append(f"{pos}: {player['First Name']} {player['Last Name']} ({player['Roster Position']}) not eligible")
            
            print(f"  {pos}: {player['First Name']} {player['Last Name']} (${player['Salary']}) - {player['Roster Position']}")
        
        print(f"  MONEY: Total Salary: ${total_salary}")
        
        if missing_players:
            print(f"  ERROR: MISSING PLAYERS: {missing_players}")
        
        if position_violations:
            print(f"  ERROR: POSITION VIOLATIONS: ")
            for violation in position_violations:
                print(f"      {violation}")
        
        if total_salary > 35000:
            print(f"  ERROR: SALARY CAP VIOLATION: ${total_salary} > $35,000")
            
        print("")
    
    print("STEP: RECOMMENDATIONS:")
    print("1. Fix position eligibility issues (e.g., catchers in OF positions)")
    print("2. Replace any missing/invalid player IDs")
    print("3. Ensure salary cap compliance")
    print("4. Verify all players are active and not IL/NS")

if __name__ == "__main__":
    diagnose_lineup_issues()

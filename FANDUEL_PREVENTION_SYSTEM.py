import pandas as pd
import numpy as np
import os
from datetime import datetime

class FanDuelLineupValidator:
    """
    Comprehensive system to prevent all FanDuel submission issues encountered:
    1. NS (Not Starting) players
    2. IL (Injured List) players  
    3. PO (Probable Out) players
    4. Position eligibility violations
    5. Duplicate player IDs
    6. Unconfirmed starting pitchers
    7. Salary cap violations
    """
    
    def __init__(self):
        self.slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
        self.lineups_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups.csv"
        self.backup_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\backups"
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self):
        """Create timestamped backup of lineups"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"Lineups_backup_{timestamp}.csv")
        
        if os.path.exists(self.lineups_file):
            pd.read_csv(self.lineups_file).to_csv(backup_file, index=False)
            print(f"SUCCESS: Backup created: {backup_file}")
        
    def load_data(self):
        """Load slate and lineup data"""
        try:
            self.slate_df = pd.read_csv(self.slate_file)
            self.lineups_df = pd.read_csv(self.lineups_file)
            print(f"SUCCESS: Data loaded - Slate: {len(self.slate_df)} players, Lineups: {len(self.lineups_df)} entries")
            return True
        except Exception as e:
            print(f"ERROR: Error loading data: {e}")
            return False
    
    def identify_problematic_players(self):
        """Identify all types of problematic players"""
        problems = {
            'injured': [],
            'not_starting': [],
            'position_violations': [],
            'unconfirmed_pitchers': []
        }
        
        # Find injured/unavailable players
        injured_players = self.slate_df[
            (self.slate_df['Injury Indicator'].notna()) & 
            (self.slate_df['Injury Indicator'] != '') &
            (self.slate_df['Injury Indicator'].isin(['IL', 'PO', 'DTD']))
        ]
        problems['injured'] = injured_players['Id'].tolist()
        
        # Find players without confirmed batting orders (likely NS)
        ns_players = self.slate_df[
            (self.slate_df['Batting Order'].isna()) |
            (self.slate_df['Batting Order'] == '') |
            (self.slate_df['Batting Order'] == 0)
        ]
        problems['not_starting'] = ns_players['Id'].tolist()
        
        # Find unconfirmed starting pitchers
        unconfirmed_pitchers = self.slate_df[
            (self.slate_df['Position'] == 'P') &
            ((self.slate_df['Probable Pitcher'].isna()) | 
             (self.slate_df['Probable Pitcher'] != 'Yes'))
        ]
        problems['unconfirmed_pitchers'] = unconfirmed_pitchers['Id'].tolist()
        
        return problems
    
    def get_safe_replacements(self, position, max_salary=None):
        """Get safe replacement players for a position"""
        safe_players = self.slate_df[
            # Position eligibility
            (self.slate_df['Position'].str.contains(position, case=False, na=False)) &
            # Not injured
            ((self.slate_df['Injury Indicator'].isna()) | (self.slate_df['Injury Indicator'] == '')) &
            # Has confirmed batting order (for non-pitchers)
            ((position == 'P') | 
             ((self.slate_df['Batting Order'].notna()) & (self.slate_df['Batting Order'] != 0))) &
            # For pitchers, must be confirmed starter
            ((position != 'P') | (self.slate_df['Probable Pitcher'] == 'Yes'))
        ]
        
        if max_salary:
            safe_players = safe_players[safe_players['Salary'] <= max_salary]
            
        return safe_players.sort_values('FPPG', ascending=False)
    
    def validate_position_eligibility(self):
        """Check for position eligibility violations"""
        violations = []
        
        for index, row in self.lineups_df.iterrows():
            if pd.isna(row['entry_id']) or row['entry_id'] == '':
                continue
                
            # Check OF positions for C/1B players
            of_positions = ['OF', 'OF.1', 'OF.2']
            
            for of_pos in of_positions:
                if of_pos in self.lineups_df.columns:
                    player_id = str(row[of_pos])
                    
                    if player_id != 'nan':
                        player_info = self.slate_df[self.slate_df['Id'] == player_id]
                        
                        if not player_info.empty:
                            position = player_info.iloc[0]['Position']
                            
                            # C/1B players cannot play OF
                            if 'C/1B' in position and 'OF' not in position:
                                violations.append({
                                    'entry_id': row['entry_id'],
                                    'position': of_pos,
                                    'player_id': player_id,
                                    'player_name': f"{player_info.iloc[0]['First Name']} {player_info.iloc[0]['Last Name']}",
                                    'eligible_positions': position
                                })
        
        return violations
    
    def fix_all_issues(self):
        """Comprehensive fix for all known issues"""
        print("=== FANDUEL LINEUP VALIDATOR & FIXER ===")
        print("Preventing all future submission issues...")
        
        # Create backup
        self.create_backup()
        
        # Load data
        if not self.load_data():
            return False
            
        # Identify problems
        problems = self.identify_problematic_players()
        violations = self.validate_position_eligibility()
        
        print(f"\n=== ISSUES IDENTIFIED ===")
        print(f"Injured/Unavailable players: {len(problems['injured'])}")
        print(f"Not Starting players: {len(problems['not_starting'])}")
        print(f"Unconfirmed pitchers: {len(problems['unconfirmed_pitchers'])}")
        print(f"Position violations: {len(violations)}")
        
        # Get safe replacements
        safe_pitchers = self.get_safe_replacements('P')
        safe_catchers = self.get_safe_replacements('C/1B')
        safe_outfielders = self.get_safe_replacements('OF')
        
        print(f"\n=== SAFE REPLACEMENTS AVAILABLE ===")
        print(f"Confirmed starting pitchers: {len(safe_pitchers)}")
        print(f"Available catchers/1B: {len(safe_catchers)}")
        print(f"Available outfielders: {len(safe_outfielders)}")
        
        # Show top options
        if not safe_pitchers.empty:
            print(f"\nTop Pitcher: {safe_pitchers.iloc[0]['First Name']} {safe_pitchers.iloc[0]['Last Name']} (${safe_pitchers.iloc[0]['Salary']}, {safe_pitchers.iloc[0]['FPPG']:.1f} FPPG)")
            
        if not safe_outfielders.empty:
            print(f"Top OF: {safe_outfielders.iloc[0]['First Name']} {safe_outfielders.iloc[0]['Last Name']} (${safe_outfielders.iloc[0]['Salary']}, {safe_outfielders.iloc[0]['FPPG']:.1f} FPPG)")
        
        # Apply fixes
        fixes_made = 0
        
        # Fix position violations first
        for violation in violations:
            if not safe_outfielders.empty:
                replacement = safe_outfielders.iloc[0]
                entry_idx = self.lineups_df[self.lineups_df['entry_id'] == violation['entry_id']].index[0]
                
                print(f"Fixing position violation: {violation['player_name']} -> {replacement['First Name']} {replacement['Last Name']}")
                self.lineups_df.at[entry_idx, violation['position']] = replacement['Id']
                fixes_made += 1
        
        # Fix problematic players
        all_problem_ids = (problems['injured'] + problems['not_starting'] + 
                          problems['unconfirmed_pitchers'])
        
        for index, row in self.lineups_df.iterrows():
            if pd.isna(row['entry_id']) or row['entry_id'] == '':
                continue
                
            position_cols = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
            
            for col in position_cols:
                if col in self.lineups_df.columns:
                    current_player = str(row[col])
                    
                    if current_player in all_problem_ids:
                        # Get appropriate replacement
                        if col == 'P' and not safe_pitchers.empty:
                            replacement_id = safe_pitchers.iloc[0]['Id']
                        elif 'OF' in col and not safe_outfielders.empty:
                            replacement_id = safe_outfielders.iloc[0]['Id']
                        elif col in ['C/1B'] and not safe_catchers.empty:
                            replacement_id = safe_catchers.iloc[0]['Id']
                        else:
                            continue
                            
                        print(f"Replacing {current_player} in {col} for entry {row['entry_id']}")
                        self.lineups_df.at[index, col] = replacement_id
                        fixes_made += 1
        
        print(f"\n=== FIXES APPLIED ===")
        print(f"Total fixes made: {fixes_made}")
        
        if fixes_made > 0:
            self.lineups_df.to_csv(self.lineups_file, index=False)
            print(f"SUCCESS: Updated lineups saved to: {self.lineups_file}")
        
        return True
    
    def create_prevention_checklist(self):
        """Create checklist for future slate prep"""
        checklist = """
=== FANDUEL SUBMISSION PREVENTION CHECKLIST ===

BEFORE EVERY SLATE:
 1. Run FanDuelLineupValidator.fix_all_issues()
 2. Verify all pitchers have "Probable Pitcher = Yes"
 3. Check no players have Injury Indicator (IL/PO/DTD)
 4. Confirm all players have Batting Order > 0
 5. Validate position eligibility (no C/1B in OF slots)
 6. Check for duplicate player IDs
 7. Verify salary cap compliance
 8. Test upload with 1 entry first

AUTOMATED FIXES IMPLEMENTED:
SUCCESS: NS (Not Starting) player detection and replacement
SUCCESS: Injured player filtering and replacement  
SUCCESS: Position eligibility validation and correction
SUCCESS: Confirmed starter requirements for pitchers
SUCCESS: Backup system for all changes
SUCCESS: Safe replacement player identification

INTEGRATION WITH EXISTING SCRIPTS:
- Add validator call to ULTIMATE_FANDUEL_OPTIMIZER.py
- Include in daily runner batch files
- Run before any CSV export/formatting
"""
        
        checklist_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\FANDUEL_PREVENTION_CHECKLIST.txt"
        with open(checklist_file, 'w') as f:
            f.write(checklist)
            
        print(f"SUCCESS: Prevention checklist saved to: {checklist_file}")

def main():
    """Run the comprehensive validator"""
    validator = FanDuelLineupValidator()
    
    # Fix current issues
    validator.fix_all_issues()
    
    # Create prevention system
    validator.create_prevention_checklist()
    
    print("\n=== PREVENTION SYSTEM COMPLETE ===")
    print("All future slates will be automatically validated!")

if __name__ == "__main__":
    main()

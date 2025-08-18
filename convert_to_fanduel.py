"""
Convert enhanced lineups to FanDuel submission format
"""

import pandas as pd
from datetime import datetime

def convert_to_fanduel_format():
    # Load the enhanced lineups
    df = pd.read_csv('../data/game_state_enhanced_lineups_20250805_185849.csv')
    
    print(f"Converting {df['lineup_id'].nunique()} lineups to FanDuel format...")
    
    # Create FanDuel submission format
    fanduel_lineups = []
    
    for lineup_id in df['lineup_id'].unique():
        lineup_data = df[df['lineup_id'] == lineup_id].copy()
        lineup_data = lineup_data.sort_values('slot')
        
        # FanDuel expects: P, C, 1B, 2B, 3B, SS, OF, OF, OF
        fanduel_row = {}
        
        for _, player in lineup_data.iterrows():
            pos = player['position']
            name = player['name']
            
            if pos == 'P':
                fanduel_row['P'] = name
            elif pos == 'C':
                fanduel_row['C'] = name
            elif pos == '1B':
                fanduel_row['1B'] = name
            elif pos == '2B':
                fanduel_row['2B'] = name
            elif pos == '3B':
                fanduel_row['3B'] = name
            elif pos == 'SS':
                fanduel_row['SS'] = name
            elif pos == 'OF':
                # Handle multiple OF positions
                if 'OF' not in fanduel_row:
                    fanduel_row['OF'] = name
                elif 'OF1' not in fanduel_row:
                    fanduel_row['OF1'] = name
                else:
                    fanduel_row['OF2'] = name
        
        # Add lineup metadata
        fanduel_row['Lineup_ID'] = f"Lineup_{lineup_id}"
        fanduel_row['Total_Salary'] = lineup_data['lineup_total_salary'].iloc[0]
        fanduel_row['Total_FPPG'] = round(lineup_data['lineup_total_projection'].iloc[0], 1)
        fanduel_row['Strategy'] = lineup_data['contest_type'].iloc[0]
        
        fanduel_lineups.append(fanduel_row)
    
    # Convert to DataFrame
    submission_df = pd.DataFrame(fanduel_lineups)
    
    # Reorder columns for FanDuel format
    columns_order = ['Lineup_ID', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF1', 'OF2', 'Total_Salary', 'Total_FPPG', 'Strategy']
    submission_df = submission_df.reindex(columns=columns_order)
    
    # Save in multiple formats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Standard FanDuel submission format
    fd_path = f"../fd_current_slate/FANDUEL_SUBMISSION_READY_{timestamp}.csv"
    submission_df.to_csv(fd_path, index=False)
    
    # Simple upload format (just names)
    simple_df = submission_df[['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF1', 'OF2']].copy()
    simple_path = f"../fd_current_slate/FD_SIMPLE_UPLOAD_{timestamp}.csv"
    simple_df.to_csv(simple_path, index=False)
    
    print(f"SUCCESS: FanDuel submission files created:")
    print(f"    Full format: {fd_path}")
    print(f"    Simple format: {simple_path}")
    print(f"   LINEUP: Ready to upload to FanDuel!")
    
    # Show top 5 lineups
    print(f"\nTARGET: TOP 5 LINEUPS FOR SUBMISSION:")
    print("="*60)
    for i, row in submission_df.head(5).iterrows():
        print(f"#{i+1} - {row['Total_FPPG']} FPPG (${row['Total_Salary']:,})")
        print(f"   P: {row['P']}")
        print(f"   C: {row['C']}")
        print(f"   1B: {row['1B']}")
        print(f"   2B: {row['2B']}")
        print(f"   3B: {row['3B']}")
        print(f"   SS: {row['SS']}")  
        print(f"   OF: {row['OF']}, {row['OF1']}, {row['OF2']}")
        print()
    
    return fd_path, simple_path

if __name__ == "__main__":
    convert_to_fanduel_format()

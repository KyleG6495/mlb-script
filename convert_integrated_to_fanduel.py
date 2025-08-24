#!/usr/bin/env python3
"""
Convert Integrated Enhanced Lineups to FanDuel Format
"""

import pandas as pd
import os
from datetime import datetime

def convert_to_fanduel():
    """Convert integrated lineups to FanDuel submission format"""
    
    # Find latest integrated lineups
    data_dir = "../data"
    files = [f for f in os.listdir(data_dir) if f.startswith('integrated_enhanced_lineups_') and f.endswith('.csv')]
    
    if not files:
        print("ERROR: No integrated lineups found to convert")
        return
    
    latest_file = max([os.path.join(data_dir, f) for f in files], key=os.path.getmtime)
    print(f"Converting: {os.path.basename(latest_file)}")
    
    # Load lineups
    df = pd.read_csv(latest_file)
    
    # Convert to FanDuel format
    fanduel_lineups = []
    
    for lineup_id in df['lineup_id'].unique():
        lineup_df = df[df['lineup_id'] == lineup_id]
        
        if len(lineup_df) == 9:  # Valid lineup
            fanduel_lineup = {
                'C': '',
                '1B': '',
                '2B': '',
                '3B': '',
                'SS': '',
                'OF': '',
                'OF ': '',
                'OF  ': '',
                'Util': ''
            }
            
            # Map players to positions (simplified)
            players = lineup_df.to_dict('records')
            
            # Fill positions (basic mapping - adapt to your position logic)
            pos_map = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF ', 'OF  ', 'Util']
            for i, player in enumerate(players):
                if i < len(pos_map):
                    name = f"{player.get('First Name', '')} {player.get('Last Name', '')}".strip()
                    if not name:
                        name = f"{player.get('Nickname', 'Player')} ({player.get('Team', 'UNK')})"
                    fanduel_lineup[pos_map[i]] = name
            
            strategy = lineup_df.iloc[0].get('strategy', 'integrated')
            fanduel_lineup['Lineup'] = f"Integrated_{lineup_id}_{strategy}"
            fanduel_lineups.append(fanduel_lineup)
    
    if fanduel_lineups:
        # Save FanDuel format
        fanduel_df = pd.DataFrame(fanduel_lineups)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../fd_current_slate/Integrated_Lineups_FD_Format_{timestamp}.csv"
        fanduel_df.to_csv(output_file, index=False)
        
        print(f"SUCCESS: Converted {len(fanduel_lineups)} lineups to FanDuel format")
        print(f"Saved: {output_file}")
    else:
        print("ERROR: No valid lineups to convert")

if __name__ == "__main__":
    convert_to_fanduel()

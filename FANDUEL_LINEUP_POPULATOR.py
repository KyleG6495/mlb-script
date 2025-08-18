#!/usr/bin/env python3
"""
FANDUEL LINEUP POPULATOR
========================
Populates the existing FanDuel Lineups.csv with our optimized lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_fanduel_lineups():
    """Populate existing FanDuel Lineups.csv with our optimized lineups"""
    
    logger.info("LINEUP: POPULATING FANDUEL LINEUPS")
    logger.info("=" * 50)
    
    # Load our lineups and FanDuel template
    lineup_file = "../data/enhanced_ml_dfs_lineups_20250812_171703.csv"
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    fanduel_template = "../fd_current_slate/Lineups.csv"
    
    try:
        # Load our lineup data
        df_lineups = pd.read_csv(lineup_file)
        logger.info(f"SUCCESS: Loaded {len(df_lineups)} lineup rows")
        
        # Load slate data for player IDs
        df_slate = pd.read_csv(slate_file)
        logger.info(f"SUCCESS: Loaded {len(df_slate)} slate players")
        
        # Load FanDuel template
        df_fanduel = pd.read_csv(fanduel_template)
        logger.info(f"SUCCESS: Loaded FanDuel template with {len(df_fanduel)} entries")
        
        # Get unique lineups (limit to available entry slots)
        unique_lineups = df_lineups['lineup_id'].unique()
        available_entries = df_fanduel[df_fanduel['entry_id'].notna() & (df_fanduel['entry_id'] != '')].copy()
        
        # Take only the entries we can fill
        max_lineups = min(len(unique_lineups), len(available_entries))
        unique_lineups = unique_lineups[:max_lineups]
        
        logger.info(f"SUCCESS: Processing {len(unique_lineups)} lineups for {len(available_entries)} entries")
        
        # Create player mapping from slate
        slate_mapping = {}
        for _, row in df_slate.iterrows():
            player_name = row.get('Nickname', '')
            player_id = row.get('Id', '')
            if player_name and player_id:
                slate_mapping[player_name] = player_id
        
        logger.info(f"SUCCESS: Created mapping for {len(slate_mapping)} players")
        
        # Process each lineup and populate FanDuel entries
        for i, lineup_id in enumerate(unique_lineups):
            if i >= len(available_entries):
                break
                
            lineup_players = df_lineups[df_lineups['lineup_id'] == lineup_id].copy()
            entry_idx = available_entries.index[i]
            
            # Initialize position assignments
            positions = {
                'P': '',
                'C/1B': '',
                '2B': '',
                '3B': '',
                'SS': '',
                'OF1': '',
                'OF2': '',
                'OF3': '',
                'UTIL': ''
            }
            
            of_count = 0
            c_player = None
            first_base_player = None
            
            # First pass: identify C and 1B players
            for _, player in lineup_players.iterrows():
                position = player['primary_position']
                name = player['name']
                player_id = slate_mapping.get(name, name)
                
                if position == 'C':
                    c_player = player_id
                elif position == '1B':
                    first_base_player = player_id
            
            # Second pass: assign all positions
            for _, player in lineup_players.iterrows():
                position = player['primary_position']
                name = player['name']
                player_id = slate_mapping.get(name, name)
                
                if position == 'P':
                    positions['P'] = player_id
                elif position == 'C':
                    positions['C/1B'] = player_id  # C takes priority in C/1B slot
                elif position == '1B':
                    if c_player:
                        positions['UTIL'] = player_id  # 1B goes to UTIL if we have C
                    else:
                        positions['C/1B'] = player_id  # 1B goes to C/1B if no C
                elif position == '2B':
                    positions['2B'] = player_id
                elif position == '3B':
                    positions['3B'] = player_id
                elif position == 'SS':
                    positions['SS'] = player_id
                elif position == 'OF':
                    if of_count == 0:
                        positions['OF1'] = player_id
                    elif of_count == 1:
                        positions['OF2'] = player_id
                    elif of_count == 2:
                        positions['OF3'] = player_id
                    else:
                        # Extra OF goes to UTIL if not already filled
                        if not positions['UTIL']:
                            positions['UTIL'] = player_id
                    of_count += 1
            
            # Update the FanDuel dataframe
            df_fanduel.loc[entry_idx, 'P'] = positions['P']
            df_fanduel.loc[entry_idx, 'C/1B'] = positions['C/1B']
            df_fanduel.loc[entry_idx, '2B'] = positions['2B']
            df_fanduel.loc[entry_idx, '3B'] = positions['3B']
            df_fanduel.loc[entry_idx, 'SS'] = positions['SS']
            df_fanduel.loc[entry_idx, 'UTIL'] = positions['UTIL']
            
            # Handle the three OF columns properly
            # Check what OF columns we actually have
            of_cols = [col for col in df_fanduel.columns if col.startswith('OF')]
            logger.info(f"Debug: OF columns found: {of_cols}")
            
            if 'OF' in df_fanduel.columns:
                df_fanduel.loc[entry_idx, 'OF'] = positions['OF1']
            if 'OF.1' in df_fanduel.columns:
                df_fanduel.loc[entry_idx, 'OF.1'] = positions['OF2']
            if 'OF.2' in df_fanduel.columns:
                df_fanduel.loc[entry_idx, 'OF.2'] = positions['OF3']
            
            # Log this lineup
            lineup_summary = lineup_players[['name', 'primary_position', 'team', 'salary', 'ml_projected_fppg']]
            total_salary = lineup_players['salary'].sum()
            total_proj = lineup_players['ml_projected_fppg'].sum()
            
            logger.info(f"\n  SUCCESS: Populated Entry {available_entries.iloc[i]['entry_id']}: ${total_salary:,} | {total_proj:.1f} FPPG")
        
        # Save the populated FanDuel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../fd_current_slate/Lineups_POPULATED_{timestamp}.csv"
        df_fanduel.to_csv(output_file, index=False)
        
        logger.info("\nTARGET: FANDUEL LINEUPS POPULATED!")
        logger.info("=" * 50)
        logger.info(f" File: {output_file}")
        logger.info(f"DATA: Populated {len(unique_lineups)} entries")
        logger.info(f"TIP: Upload this file to FanDuel or copy the rows manually")
        
        # Show summary of top 3 lineups
        logger.info("\nLINEUP: TOP 3 POPULATED LINEUPS:")
        for i in range(min(3, len(unique_lineups))):
            lineup_id = unique_lineups[i]
            lineup_players = df_lineups[df_lineups['lineup_id'] == lineup_id]
            total_salary = lineup_players['salary'].sum()
            total_proj = lineup_players['ml_projected_fppg'].sum()
            contest_type = lineup_players['contest_type'].iloc[0]
            entry_id = available_entries.iloc[i]['entry_id']
            
            logger.info(f"\n  Entry {entry_id} - Lineup {lineup_id} ({contest_type}): ${total_salary:,} | {total_proj:.1f} FPPG")
            for _, player in lineup_players.iterrows():
                pos = player['primary_position']
                name = player['name']
                team = player['team']
                salary = player['salary']
                proj = player['ml_projected_fppg']
                logger.info(f"    {pos:>3}: {name:<20} ({team}) - ${salary:,} - {proj:.1f} pts")
        
        return output_file
        
    except Exception as e:
        logger.error(f"ERROR: Error populating FanDuel lineups: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    populate_fanduel_lineups()

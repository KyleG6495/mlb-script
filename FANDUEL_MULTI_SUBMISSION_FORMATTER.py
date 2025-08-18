#!/usr/bin/env python3
"""
FANDUEL MULTI-LINEUP SUBMISSION FORMATTER
=========================================
Creates properly formatted CSV files for FanDuel lineup submission with multiple lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fanduel_multi_submission():
    """Create proper FanDuel submission format with multiple lineups"""
    
    logger.info("LINEUP: CREATING FANDUEL MULTI-LINEUP SUBMISSION")
    logger.info("=" * 60)
    
    # Load our lineups
    lineup_file = "../data/enhanced_ml_dfs_lineups_20250812_171703.csv"
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    
    try:
        # Load lineup data
        df_lineups = pd.read_csv(lineup_file)
        logger.info(f"SUCCESS: Loaded {len(df_lineups)} lineup rows")
        
        # Load slate data for player IDs
        df_slate = pd.read_csv(slate_file)
        logger.info(f"SUCCESS: Loaded {len(df_slate)} slate players")
        
        # Get unique lineups (limit to top 10 for submission)
        unique_lineups = df_lineups['lineup_id'].unique()[:10]
        logger.info(f"SUCCESS: Processing {len(unique_lineups)} lineups for submission")
        
        # Create player mapping from slate
        slate_mapping = {}
        for _, row in df_slate.iterrows():
            player_name = row.get('Nickname', '')
            player_id = row.get('Id', '')
            if player_name and player_id:
                slate_mapping[player_name] = player_id
        
        logger.info(f"SUCCESS: Created mapping for {len(slate_mapping)} players")
        
        # Build FanDuel submission format for all lineups
        all_submission_rows = []
        
        for lineup_id in unique_lineups:
            lineup_players = df_lineups[df_lineups['lineup_id'] == lineup_id].copy()
            
            # Initialize lineup dictionary with FanDuel's exact format
            fanduel_lineup = {
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
            
            # First pass: collect all players
            for _, player in lineup_players.iterrows():
                position = player['primary_position']
                name = player['name']
                player_id = slate_mapping.get(name, name)  # Use ID if available
                
                if position == 'C':
                    c_player = player_id
                elif position == '1B':
                    first_base_player = player_id
            
            # Second pass: assign positions
            for _, player in lineup_players.iterrows():
                position = player['primary_position']
                name = player['name']
                player_id = slate_mapping.get(name, name)  # Use ID if available
                
                # Map positions to FanDuel format
                if position == 'P':
                    fanduel_lineup['P'] = player_id
                elif position == 'C':
                    # C goes to C/1B position (priority over 1B)
                    fanduel_lineup['C/1B'] = player_id
                elif position == '1B':
                    # If we have a C, 1B goes to UTIL; otherwise 1B goes to C/1B
                    if c_player:
                        fanduel_lineup['UTIL'] = player_id
                    else:
                        fanduel_lineup['C/1B'] = player_id
                elif position == '2B':
                    fanduel_lineup['2B'] = player_id
                elif position == '3B':
                    fanduel_lineup['3B'] = player_id
                elif position == 'SS':
                    fanduel_lineup['SS'] = player_id
                elif position == 'OF':
                    # Handle multiple OF positions
                    if of_count == 0:
                        fanduel_lineup['OF1'] = player_id
                    elif of_count == 1:
                        fanduel_lineup['OF2'] = player_id
                    elif of_count == 2:
                        fanduel_lineup['OF3'] = player_id
                    else:
                        # Extra OF goes to UTIL
                        fanduel_lineup['UTIL'] = player_id
                    of_count += 1
            
            # Add this lineup to submission
            all_submission_rows.append(fanduel_lineup)
        
        # Create DataFrame with correct FanDuel column structure
        # Note: pandas reads duplicate 'OF' columns as 'OF', 'OF.1', 'OF.2'
        submission_data = []
        
        for fanduel_lineup in all_submission_rows:
            row = [
                fanduel_lineup['P'],
                fanduel_lineup['C/1B'],
                fanduel_lineup['2B'],
                fanduel_lineup['3B'],
                fanduel_lineup['SS'],
                fanduel_lineup['OF1'],
                fanduel_lineup['OF2'],
                fanduel_lineup['OF3'],
                fanduel_lineup['UTIL']
            ]
            submission_data.append(row)
        
        # Create DataFrame with correct column names to match FanDuel format
        df_submission = pd.DataFrame(submission_data, 
                                   columns=['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL'])
        
        # Save FanDuel submission file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/FANDUEL_MULTI_SUBMISSION_{timestamp}.csv"
        df_submission.to_csv(output_file, index=False)
        
        logger.info("TARGET: FANDUEL MULTI-LINEUP SUBMISSION CREATED")
        logger.info("=" * 60)
        logger.info(f" File: {output_file}")
        logger.info(f"DATA: Total Lineups: {len(df_submission)}")
        
        # Show top 3 lineups
        logger.info("\nLINEUP: TOP 3 LINEUPS:")
        for i, lineup_id in enumerate(unique_lineups[:3]):
            lineup_players = df_lineups[df_lineups['lineup_id'] == lineup_id]
            total_salary = lineup_players['salary'].sum()
            total_proj = lineup_players['ml_projected_fppg'].sum()
            contest_type = lineup_players['contest_type'].iloc[0]
            
            logger.info(f"\n  Lineup {lineup_id} ({contest_type}): ${total_salary:,} | {total_proj:.1f} FPPG")
            for _, player in lineup_players.iterrows():
                logger.info(f"    {player['primary_position']:>3}: {player['name']:<20} ({player['team']}) - ${player['salary']:,}")
        
        # Also create a readable summary
        readable_data = []
        for i, lineup_id in enumerate(unique_lineups):
            lineup_players = df_lineups[df_lineups['lineup_id'] == lineup_id]
            total_salary = lineup_players['salary'].sum()
            total_proj = lineup_players['ml_projected_fppg'].sum()
            contest_type = lineup_players['contest_type'].iloc[0]
            
            readable_data.append({
                'Lineup_ID': lineup_id,
                'Contest_Type': contest_type,
                'Total_Salary': f"${total_salary:,}",
                'Total_Projection': f"{total_proj:.1f}",
                'Players': " | ".join([f"{p['name']} ({p['primary_position']})" for _, p in lineup_players.iterrows()])
            })
        
        df_readable = pd.DataFrame(readable_data)
        readable_file = f"../data/FANDUEL_LINEUPS_SUMMARY_{timestamp}.csv"
        df_readable.to_csv(readable_file, index=False)
        
        logger.info(f"\nINFO: Summary file: {readable_file}")
        logger.info("\nSUCCESS: READY FOR FANDUEL MULTI-LINEUP SUBMISSION!")
        logger.info("TIP: Copy and paste all rows from the submission file into FanDuel")
        
        return output_file, readable_file
        
    except Exception as e:
        logger.error(f"ERROR: Error creating FanDuel submission: {e}")
        return None, None

if __name__ == "__main__":
    create_fanduel_multi_submission()

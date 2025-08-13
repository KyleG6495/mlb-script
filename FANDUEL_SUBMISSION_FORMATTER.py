#!/usr/bin/env python3
"""
FANDUEL SUBMISSION FORMATTER
============================
Creates properly formatted CSV files for FanDuel lineup submission
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fanduel_submission():
    """Create proper FanDuel submission format"""
    
    logger.info("🏆 CREATING FANDUEL SUBMISSION FORMAT")
    logger.info("=" * 50)
    
    # Load our best lineup
    lineup_file = "../data/enhanced_ml_dfs_lineups_20250812_171703.csv"
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    
    try:
        # Load lineup data
        df_lineups = pd.read_csv(lineup_file)
        logger.info(f"✅ Loaded {len(df_lineups)} lineup rows")
        
        # Load slate data for player IDs
        df_slate = pd.read_csv(slate_file)
        logger.info(f"✅ Loaded {len(df_slate)} slate players")
        
        # Get all unique lineups for submission
        unique_lineups = df_lineups['lineup_id'].unique()
        logger.info(f"✅ Found {len(unique_lineups)} unique lineups")
        
        # Create player mapping from slate
        slate_mapping = {}
        for _, row in df_slate.iterrows():
            player_name = row.get('Nickname', '')
            player_id = row.get('Id', '')
            if player_name and player_id:
                slate_mapping[player_name] = player_id
        
        logger.info(f"✅ Created mapping for {len(slate_mapping)} players")
        
        # Get the best lineup (highest projected points)
        best_lineup_id = df_lineups.groupby('lineup_id')['ml_projected_fppg'].sum().idxmax()
        best_lineup = df_lineups[df_lineups['lineup_id'] == best_lineup_id].copy()
        
        # Initialize FanDuel lineup dictionary
        fanduel_lineup = {}
        
        # Build FanDuel submission format for the best lineup
        for _, player in best_lineup.iterrows():
            position = player['primary_position']
            name = player['name']
            player_id = slate_mapping.get(name, name)  # Use ID if available, name otherwise
            
            # Map positions to FanDuel format
            if position == 'P':
                fanduel_lineup['P'] = player_id
            elif position == 'C':
                fanduel_lineup['C'] = player_id
            elif position == '1B':
                fanduel_lineup['1B'] = player_id
            elif position == '2B':
                fanduel_lineup['2B'] = player_id
            elif position == '3B':
                fanduel_lineup['3B'] = player_id
            elif position == 'SS':
                fanduel_lineup['SS'] = player_id
            elif position == 'OF':
                # Handle multiple OF positions
                if 'OF' not in fanduel_lineup:
                    fanduel_lineup['OF'] = player_id
                elif 'OF_2' not in fanduel_lineup:
                    fanduel_lineup['OF_2'] = player_id
                elif 'OF_3' not in fanduel_lineup:
                    fanduel_lineup['OF_3'] = player_id
        
        # Create DataFrame in FanDuel format
        submission_data = {
            'P': [fanduel_lineup.get('P', '')],
            'C': [fanduel_lineup.get('C', '')],
            '1B': [fanduel_lineup.get('1B', '')],
            '2B': [fanduel_lineup.get('2B', '')],
            '3B': [fanduel_lineup.get('3B', '')],
            'SS': [fanduel_lineup.get('SS', '')],
            'OF': [fanduel_lineup.get('OF', '')],
            'OF_2': [fanduel_lineup.get('OF_2', '')],
            'OF_3': [fanduel_lineup.get('OF_3', '')]
        }
        
        df_submission = pd.DataFrame(submission_data)
        
        # Save FanDuel submission file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/FANDUEL_SUBMISSION_{timestamp}.csv"
        df_submission.to_csv(output_file, index=False)
        
        logger.info("🎯 FANDUEL SUBMISSION CREATED")
        logger.info("=" * 50)
        logger.info(f"📁 File: {output_file}")
        logger.info("\n🏆 LINEUP FOR FANDUEL:")
        
        # Show lineup details
        for _, player in best_lineup.iterrows():
            pos = player['primary_position']
            name = player['name']
            team = player['team']
            salary = player['salary']
            proj = player['ml_projected_fppg']
            logger.info(f"  {pos:>3}: {name:<20} ({team}) - ${salary:,} - {proj:.1f} pts")
        
        total_salary = best_lineup['salary'].sum()
        total_proj = best_lineup['ml_projected_fppg'].sum()
        logger.info(f"\n💰 Total Salary: ${total_salary:,}")
        logger.info(f"📊 Total Projection: {total_proj:.1f} FPPG")
        
        # Also create a readable format
        readable_data = []
        for _, player in best_lineup.iterrows():
            readable_data.append({
                'Position': player['primary_position'],
                'Player': player['name'],
                'Team': player['team'],
                'Salary': f"${player['salary']:,}",
                'Projection': f"{player['ml_projected_fppg']:.1f}"
            })
        
        df_readable = pd.DataFrame(readable_data)
        readable_file = f"../data/FANDUEL_LINEUP_READABLE_{timestamp}.csv"
        df_readable.to_csv(readable_file, index=False)
        
        logger.info(f"📋 Readable format: {readable_file}")
        logger.info("\n✅ READY FOR FANDUEL SUBMISSION!")
        
        return output_file, readable_file
        
    except Exception as e:
        logger.error(f"❌ Error creating FanDuel submission: {e}")
        return None, None

if __name__ == "__main__":
    create_fanduel_submission()

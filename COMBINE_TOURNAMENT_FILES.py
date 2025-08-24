#!/usr/bin/env python3
"""
WORKING TOURNAMENT COMBINER
Combines your existing safe enhanced tournament files into a master portfolio
"""
import pandas as pd
import glob
import os
from datetime import datetime

def main():
    print(' Looking for safe enhanced tournament files...')
    
    # Look for files from today - try multiple path patterns
    patterns = [
        '../fd_current_slate/SAFE_ENHANCED_TOURNAMENT_20250801_*.csv',
        'c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/SAFE_ENHANCED_TOURNAMENT_20250801_*.csv',
        './fd_current_slate/SAFE_ENHANCED_TOURNAMENT_20250801_*.csv'
    ]
    
    files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            break
    
    if not files:
        print('ERROR: No safe enhanced tournament files found for today')
        print('TIP: Try running: python ../SAFE_ENHANCED_TOURNAMENT_GENERATOR.py')
        return False
    
    print(f'SUCCESS: Found {len(files)} safe enhanced tournament files')
    
    all_lineups = []
    lineup_counter = 1
    
    for i, file in enumerate(sorted(files)):
        print(f'DATA: Processing file {i+1}: {os.path.basename(file)}')
        df = pd.read_csv(file)
        
        # Update lineup IDs to be sequential
        unique_lineups = df['lineup_id'].nunique()
        df['lineup_id'] = df['lineup_id'] + lineup_counter - 1
        df['Lineup_ID'] = df['Lineup_ID'] + lineup_counter - 1
        lineup_counter += unique_lineups
        all_lineups.append(df)
    
    # Combine all lineups
    combined = pd.concat(all_lineups, ignore_index=True)
    
    # Save master file - try multiple output paths
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_paths = [
        f'../fd_current_slate/MASTER_SAFE_TOURNAMENT_{timestamp}.csv',
        f'c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/MASTER_SAFE_TOURNAMENT_{timestamp}.csv'
    ]
    
    output_file = None
    for path in output_paths:
        try:
            combined.to_csv(path, index=False)
            output_file = path
            break
        except (OSError, FileNotFoundError):
            continue
    
    if output_file is None:
        # Create directory if needed and try again
        os.makedirs('../fd_current_slate', exist_ok=True)
        output_file = f'../fd_current_slate/MASTER_SAFE_TOURNAMENT_{timestamp}.csv'
        combined.to_csv(output_file, index=False)
    
    # Calculate stats
    total_lineups = combined['lineup_id'].nunique()
    min_proj = combined['Projected_FPPG'].min()
    max_proj = combined['Projected_FPPG'].max()
    avg_proj = combined.groupby('lineup_id')['Projected_FPPG'].sum().mean()
    
    print(f'SUCCESS: Master tournament file created: {os.path.basename(output_file)}')
    print(f'LINEUP: Total lineups: {total_lineups}')
    print(f'MONEY: Projection range: {min_proj:.1f} - {max_proj:.1f} FPPG')
    print(f'DATA: Average lineup score: {avg_proj:.1f} FPPG')
    print(f'TARGET: File location: {output_file}')
    
    # Also create a FanDuel submission format
    submission_paths = [
        f'../fd_current_slate/FD_SUBMISSION_READY_{timestamp}.csv',
        f'c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/FD_SUBMISSION_READY_{timestamp}.csv'
    ]
    
    submission_file = None
    fanduel_format = combined[['Id', 'Position', 'First Name', 'Nickname', 'Last Name', 
                              'FPPG', 'Played', 'Salary', 'Game', 'Team', 'Opponent', 
                              'Injury Indicator', 'Injury Details', 'Tier', 'Probable Pitcher', 
                              'Batting Order', 'Roster Position', 'Lineup_ID']]
    
    for path in submission_paths:
        try:
            fanduel_format.to_csv(path, index=False)
            submission_file = path
            break
        except (OSError, FileNotFoundError):
            continue
    print(f'INFO: FanDuel submission format: {os.path.basename(submission_file)}')
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print('\nSTART: SUCCESS: Tournament files ready for submission!')
    else:
        print('\nERROR: Failed to combine files - but individual files may still be available')

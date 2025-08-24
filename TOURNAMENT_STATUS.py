#!/usr/bin/env python3
"""
Tournament Status Checker
Shows the final tournament portfolio status
"""
import glob
import pandas as pd
import os

def main():
    # Check latest master file
    master_files = glob.glob('../fd_current_slate/MASTER_SAFE_TOURNAMENT_*.csv')
    if master_files:
        latest_file = max(master_files)
        df = pd.read_csv(latest_file)
        total_lineups = df['lineup_id'].nunique()
        min_proj = df['Projected_FPPG'].min()
        max_proj = df['Projected_FPPG'].max()
        avg_proj = df.groupby('lineup_id')['Projected_FPPG'].sum().mean()
        
        print(f' Latest Master File: {os.path.basename(latest_file)}')
        print(f'LINEUP: Total Tournament Lineups: {total_lineups}')
        print(f'MONEY: Projection Range: {min_proj:.1f} - {max_proj:.1f} FPPG')
        print(f'DATA: Average Lineup Score: {avg_proj:.1f} FPPG')
        print(f'SUCCESS: Ready for tournament submission!')
    else:
        print('WARNING: No master tournament file found')

if __name__ == "__main__":
    main()

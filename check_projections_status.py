#!/usr/bin/env python3
"""
Check projection files status
"""
import pandas as pd
import os

print('=== PROJECTION FILES STATUS ===')
print()

# Check what projection files exist
data_dir = '../data'
files = os.listdir(data_dir)

projection_files = [f for f in files if any(keyword in f.lower() for keyword in ['projection', 'features_final', 'ml_dfs'])]
print('Projection-related files:')
for f in sorted(projection_files):
    if f.endswith('.csv'):
        try:
            df = pd.read_csv(os.path.join(data_dir, f))
            print(f'  {f}: {df.shape[0]} rows, {df.shape[1]} columns')
        except:
            print(f'  {f}: Error reading')

print()
print('=== FD FEATURES FILES ===')

# Check specifically the FD feature files
hitter_file = '../data/fd_hitter_features_final.csv'
pitcher_file = '../data/fd_pitcher_features_final.csv'

if os.path.exists(hitter_file):
    hitters = pd.read_csv(hitter_file)
    print(f'Hitters: {len(hitters)} players')
    
    # Check projection columns
    proj_cols = [col for col in hitters.columns if any(keyword in col.lower() for keyword in ['fppg', 'proj', 'score'])]
    print(f'  Projection columns: {proj_cols}')
    
    if 'Projected_FPPG' in hitters.columns:
        non_zero = (hitters['Projected_FPPG'] > 0).sum()
        print(f'  Non-zero Projected_FPPG: {non_zero}/{len(hitters)}')
        if non_zero > 0:
            min_val = hitters[hitters['Projected_FPPG'] > 0]['Projected_FPPG'].min()
            max_val = hitters[hitters['Projected_FPPG'] > 0]['Projected_FPPG'].max()
            print(f'  Range: {min_val:.2f} - {max_val:.2f}')
else:
    print('❌ fd_hitter_features_final.csv not found')

if os.path.exists(pitcher_file):
    pitchers = pd.read_csv(pitcher_file)
    print(f'Pitchers: {len(pitchers)} players')
    
    # Check if pitchers have projections
    if 'FPPG' in pitchers.columns:
        non_zero = (pitchers['FPPG'] > 0).sum()
        print(f'  Non-zero FPPG: {non_zero}/{len(pitchers)}')
        if non_zero > 0:
            min_val = pitchers[pitchers['FPPG'] > 0]['FPPG'].min()
            max_val = pitchers[pitchers['FPPG'] > 0]['FPPG'].max()
            print(f'  Range: {min_val:.2f} - {max_val:.2f}')
    
    proj_cols = [col for col in pitchers.columns if any(keyword in col.lower() for keyword in ['fppg', 'proj', 'score'])]
    print(f'  Projection columns: {proj_cols}')
else:
    print('❌ fd_pitcher_features_final.csv not found')

print()
print('=== MOST RECENT ML PROJECTIONS ===')

# Check recent ML projection files
ml_files = [f for f in files if 'ml_dfs' in f.lower() and f.endswith('.csv')]
if ml_files:
    latest_ml = max(ml_files)
    print(f'Latest ML file: {latest_ml}')
    
enhanced_files = [f for f in files if 'enhanced_ml' in f.lower() and f.endswith('.csv')]
if enhanced_files:
    latest_enhanced = max(enhanced_files)
    print(f'Latest Enhanced file: {latest_enhanced}')

print()
print('=== THE REAL QUESTION ===')
print('Do we have actual ML-generated projections with realistic FPPG values?')
print('OR are we using placeholder/estimated values?')

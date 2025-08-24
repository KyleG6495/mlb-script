#!/usr/bin/env python3
"""
Fix pitcher projections by adding Projected_FPPG column
"""
import pandas as pd

# Fix pitcher projections by adding Projected_FPPG column
pitchers = pd.read_csv('../data/fd_pitcher_features_final.csv')

print('FIXING PITCHER PROJECTIONS...')
print(f'Before: {len(pitchers)} pitchers')
print('Columns before:', [col for col in pitchers.columns if 'fppg' in col.lower() or 'proj' in col.lower()])

# Add Projected_FPPG column by copying FPPG
pitchers['Projected_FPPG'] = pitchers['FPPG']

print('Columns after:', [col for col in pitchers.columns if 'fppg' in col.lower() or 'proj' in col.lower()])
non_zero = (pitchers['Projected_FPPG'] > 0).sum()
total = len(pitchers)
min_val = pitchers['Projected_FPPG'].min()
max_val = pitchers['Projected_FPPG'].max()
print(f'Projected_FPPG values: {non_zero}/{total} non-zero')
print(f'Range: {min_val:.2f} - {max_val:.2f}')

# Save updated pitcher file
pitchers.to_csv('../data/fd_pitcher_features_final.csv', index=False)
print('✅ SAVED: Updated pitcher features with Projected_FPPG column')

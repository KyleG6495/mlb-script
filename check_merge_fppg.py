#!/usr/bin/env python3
"""
Check FPPG values in merged data
"""
import pandas as pd

# Check the merged data FPPG values
slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
slate_filtered = slate[(slate['Tier'] != 'Late Swap') & (slate['Injury Indicator'].isna() | (slate['Injury Indicator'] == ''))].copy()

hitters = pd.read_csv('../data/fd_hitter_features_final.csv')
pitchers = pd.read_csv('../data/fd_pitcher_features_final.csv')
projections = pd.concat([hitters, pitchers], ignore_index=True)

# Test merge
df = slate_filtered.merge(projections, on='Id', how='left', suffixes=('', '_proj'))

print('MERGE ANALYSIS:')
print('Slate filtered:', len(slate_filtered))
print('Projections:', len(projections))
print('After merge:', len(df))
print()

# Check FPPG columns
fppg_cols = [col for col in df.columns if 'fppg' in col.lower() or 'projection' in col.lower()]
print('FPPG columns after merge:', fppg_cols)
print()

# Check values in different FPPG columns
for col in ['FPPG', 'FPPG_proj', 'Projected_FPPG']:
    if col in df.columns:
        non_null = df[col].notna().sum()
        if non_null > 0:
            min_val = df[col].min()
            max_val = df[col].max()
            zero_count = (df[col] == 0).sum()
            print(f'{col}: {non_null}/{len(df)} non-null, range {min_val:.2f}-{max_val:.2f}, {zero_count} zeros')
        else:
            print(f'{col}: All null')

# Check what projection column the system should use
proj_cols = ['projected_fppg', 'FPPG', 'fppg', 'projection']
proj_col = None
for col in proj_cols:
    if col in df.columns:
        proj_col = col
        break

print()
print('System would use projection column:', proj_col)

# Show sample data
print()
print('Sample merged data with projections:')
with_proj = df[df['Projected_FPPG'].notna()].head(3) if 'Projected_FPPG' in df.columns else df.head(3)
if len(with_proj) > 0:
    print(with_proj[['Id', 'Nickname', 'Position', 'Salary', 'FPPG', 'Projected_FPPG']].to_string())
else:
    print("No merged data with projections found")

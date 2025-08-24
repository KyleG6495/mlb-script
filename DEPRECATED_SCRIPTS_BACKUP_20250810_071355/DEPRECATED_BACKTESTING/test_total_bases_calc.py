#!/usr/bin/env python3
"""Test total_bases calculation on prediction features"""

import pandas as pd

# Load prediction features
df = pd.read_csv('../data/prediction_features_enhanced_real_stats.csv')

# Calculate total_bases like the system does
df['totalBases_calc'] = (
    df.get('hits', 0) + 
    df.get('doubles', 0) * 2 + 
    df.get('triples', 0) * 3 + 
    df.get('homeRuns', 0) * 4
)

print('Calculated totalBases stats:')
print(f'Mean: {df["totalBases_calc"].mean():.3f}')
print(f'Min: {df["totalBases_calc"].min():.3f}')
print(f'Max: {df["totalBases_calc"].max():.3f}')
print(f'Std: {df["totalBases_calc"].std():.3f}')

print('\nSample values:')
print(df[['name', 'totalBases_calc']].head(10))

print('\nValue distribution:')
print(df['totalBases_calc'].value_counts().sort_index())

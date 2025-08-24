#!/usr/bin/env python3
"""
validate_predictions.py

Validate that all model predictions are within reasonable ranges
"""
import pandas as pd
import numpy as np

def validate_predictions():
    print(" VALIDATING BETTING PREDICTIONS")
    print("="*50)
    
    # Load latest betting opportunities
    df = pd.read_csv("./betting_analysis/betting_opportunities_20250725_183855.csv")
    
    # Reasonable ranges for each stat
    ranges = {
        'hits': (0, 6),
        'total_bases': (0, 15),
        'runs': (0, 6),
        'rbi': (0, 8),
        'home_runs': (0, 4),
        'hitter_strikeouts': (0, 6)
    }
    
    for category in ranges.keys():
        cat_data = df[df['category'] == category]
        if len(cat_data) == 0:
            continue
            
        min_pred = cat_data['prediction'].min()
        max_pred = cat_data['prediction'].max()
        mean_pred = cat_data['prediction'].mean()
        
        min_expected, max_expected = ranges[category]
        
        print(f"\nDATA: {category.upper()}:")
        print(f"  Predictions: {min_pred:.2f} - {max_pred:.2f} (avg: {mean_pred:.2f})")
        print(f"  Expected:    {min_expected} - {max_expected}")
        
        # Flag issues
        if min_pred < min_expected:
            print(f"  WARNING:  ISSUE: Minimum prediction {min_pred:.2f} below expected {min_expected}")
        if max_pred > max_expected:
            print(f"  WARNING:  ISSUE: Maximum prediction {max_pred:.2f} above expected {max_expected}")
        if min_pred < 0:
            print(f"  ERROR: ERROR: Negative predictions found!")
        
        # Show sample lines
        sample_lines = cat_data['line'].unique()[:10]
        print(f"  Sample lines: {sorted(sample_lines)}")
        
        # Check for repeated predictions (could indicate model issues)
        unique_preds = len(cat_data['prediction'].unique())
        total_preds = len(cat_data)
        diversity = unique_preds / total_preds
        print(f"  Prediction diversity: {unique_preds}/{total_preds} ({diversity:.2%})")
        
        if diversity < 0.5:
            print(f"  WARNING:  WARNING: Low prediction diversity - possible model overfitting")

if __name__ == "__main__":
    validate_predictions()

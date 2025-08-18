#!/usr/bin/env python3
"""
Debug Enhanced Optimizer - Check Data Issues
"""

import pandas as pd
import numpy as np

def debug_enhanced_optimizer():
    print(" DEBUGGING ENHANCED OPTIMIZER")
    print("=" * 40)
    
    # Load slate data
    slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    print(f"Original slate: {len(slate_df)} players")
    
    # Check basic columns
    print("\nColumn analysis:")
    print(f"- Salary range: ${slate_df['Salary'].min():,} to ${slate_df['Salary'].max():,}")
    print(f"- FPPG range: {slate_df['FPPG'].min():.1f} to {slate_df['FPPG'].max():.1f}")
    print(f"- Injury indicators: {slate_df['Injury Indicator'].value_counts().to_dict()}")
    
    # Simulate the enhanced processing
    print("\n Simulating enhancement process...")
    
    # Step 1: Add features
    try:
        features_df = pd.read_csv("../data/prediction_features_enhanced_real_stats.csv")
        print(f"SUCCESS: Features loaded: {len(features_df)} players")
    except:
        print("WARNING: Features not found")
    
    # Step 2: Create projections
    slate_df['Base_Projection'] = slate_df['FPPG']  # Use existing FPPG
    print(f"Base projections created: {slate_df['Base_Projection'].mean():.1f} avg")
    
    # Step 3: Real-time adjustments (simplified)
    adjustments = np.random.uniform(0.8, 1.2, len(slate_df))
    slate_df['Real_Time_FPPG'] = slate_df['Base_Projection'] * adjustments
    print(f"Real-time adjusted: {slate_df['Real_Time_FPPG'].mean():.1f} avg")
    
    # Step 4: Final projections
    slate_df['Projected_FPPG'] = slate_df['Real_Time_FPPG']
    print(f"Final projections: {slate_df['Projected_FPPG'].mean():.1f} avg")
    
    # Step 5: Test filtering
    print("\n Testing filtering criteria...")
    
    salary_filter = slate_df['Salary'] >= 2000
    proj_filter = slate_df['Projected_FPPG'] > 0
    injury_filter = (~slate_df['Injury Indicator'].isin(['IL', 'DTD']) | slate_df['Injury Indicator'].isna())
    
    print(f"Salary >= 2000: {salary_filter.sum()} players")
    print(f"Projected_FPPG > 0: {proj_filter.sum()} players")
    print(f"Not injured: {injury_filter.sum()} players")
    
    eligible = slate_df[salary_filter & proj_filter & injury_filter]
    print(f"Combined eligible: {len(eligible)} players")
    
    if len(eligible) > 0:
        print("\nSUCCESS: Eligible players found!")
        print(f"Position breakdown: {eligible['Position'].value_counts().head(10).to_dict()}")
        
        # Test position mapping
        def get_primary_position(position_str):
            if pd.isna(position_str):
                return 'OF'
            
            pos_str = str(position_str).upper()
            
            if 'P' in pos_str:
                return 'P'
            elif 'C' in pos_str and '1B' not in pos_str:
                return 'C'
            elif '1B' in pos_str:
                return '1B'
            elif '2B' in pos_str and 'SS' not in pos_str and '3B' not in pos_str:
                return '2B'
            elif '3B' in pos_str and '2B' not in pos_str and 'SS' not in pos_str:
                return '3B'
            elif 'SS' in pos_str and '2B' not in pos_str and '3B' not in pos_str:
                return 'SS'
            else:
                return 'OF'
        
        eligible['Primary_Position'] = eligible['Position'].apply(get_primary_position)
        print(f"Primary positions: {eligible['Primary_Position'].value_counts().to_dict()}")
        
        # Check requirements
        position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        
        for pos, min_needed in position_requirements.items():
            available = len(eligible[eligible['Primary_Position'] == pos])
            status = "SUCCESS:" if available >= min_needed else "ERROR:"
            print(f"{status} {pos}: {available} available (need {min_needed})")
    
    else:
        print("\nERROR: No eligible players found!")
        print("Checking individual criteria...")
        
        print(f"Players with Salary >= 2000: {salary_filter.sum()}")
        print(f"Players with Projected_FPPG > 0: {proj_filter.sum()}")
        print(f"Players not injured: {injury_filter.sum()}")
        
        if proj_filter.sum() == 0:
            print(f"\n ISSUE: All Projected_FPPG values are <= 0")
            print(f"Projected_FPPG stats: min={slate_df['Projected_FPPG'].min():.3f}, max={slate_df['Projected_FPPG'].max():.3f}")
        
        if salary_filter.sum() == 0:
            print(f"\n ISSUE: All salaries are < 2000")
            print(f"Salary stats: min=${slate_df['Salary'].min()}, max=${slate_df['Salary'].max()}")

if __name__ == "__main__":
    debug_enhanced_optimizer()

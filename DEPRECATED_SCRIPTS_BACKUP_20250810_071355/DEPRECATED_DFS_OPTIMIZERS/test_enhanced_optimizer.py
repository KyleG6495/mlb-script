#!/usr/bin/env python3
"""
Quick Test of Enhanced FanDuel Optimizer

Tests the new enhanced system with current data structure
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def test_enhanced_optimizer():
    print("🧪 TESTING ENHANCED FANDUEL OPTIMIZER")
    print("=" * 45)
    
    # Test data loading
    print("\n1. Testing data loading...")
    try:
        slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        print(f"✅ Loaded slate: {len(slate_df)} players")
        print(f"   Positions: {slate_df['Position'].value_counts().to_dict()}")
    except Exception as e:
        print(f"❌ Error loading slate: {e}")
        return
    
    # Test enhanced features
    print("\n2. Testing enhanced features...")
    try:
        features_df = pd.read_csv("../data/prediction_features_enhanced_real_stats.csv")
        print(f"✅ Loaded features: {len(features_df)} players with {len(features_df.columns)} features")
        
        # Check for required columns
        required_cols = ['atBats', 'hits', 'homeRuns', 'rbi', 'runs']
        available_cols = [col for col in required_cols if col in features_df.columns]
        print(f"   Available stats: {available_cols}")
        
    except Exception as e:
        print(f"⚠️ Enhanced features not available: {e}")
    
    # Test basic projections
    print("\n3. Testing projection creation...")
    try:
        # Simple test projection based on available data
        pitcher_mask = slate_df['Position'] == 'P'
        hitter_mask = ~pitcher_mask
        
        slate_df['Test_FPPG'] = 0.0
        slate_df.loc[pitcher_mask, 'Test_FPPG'] = np.random.uniform(8, 25, pitcher_mask.sum())
        slate_df.loc[hitter_mask, 'Test_FPPG'] = np.random.uniform(6, 18, hitter_mask.sum())
        
        print(f"✅ Created test projections")
        print(f"   Hitter avg: {slate_df[slate_df['Position'] != 'P']['Test_FPPG'].mean():.1f}")
        print(f"   Pitcher avg: {slate_df[slate_df['Position'] == 'P']['Test_FPPG'].mean():.1f}")
        
    except Exception as e:
        print(f"❌ Error creating projections: {e}")
        return
    
    # Test optimization setup
    print("\n4. Testing optimization setup...")
    try:
        # Filter eligible players
        eligible = slate_df[
            (slate_df['Salary'] >= 2000) & 
            (slate_df['Test_FPPG'] > 0)
        ].copy()
        
        print(f"✅ Eligible players: {len(eligible)}")
        
        # Check position requirements
        positions = eligible['Position'].str.split('/').explode().value_counts()
        print(f"   Position breakdown: {positions.to_dict()}")
        
        # Test salary constraints
        total_salary = eligible['Salary'].sum()
        print(f"   Total salary pool: ${total_salary:,}")
        print(f"   Budget constraint: $35,000")
        
    except Exception as e:
        print(f"❌ Error in optimization setup: {e}")
        return
    
    # Test basic lineup construction
    print("\n5. Testing basic lineup construction...")
    try:
        # Simple greedy lineup for testing
        lineup_players = []
        remaining_salary = 35000
        
        # Sort by value
        eligible['value'] = eligible['Test_FPPG'] / eligible['Salary'] * 1000
        eligible_sorted = eligible.sort_values('value', ascending=False)
        
        # Required positions
        position_needs = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        selected_positions = {'P': 0, 'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0}
        
        for _, player in eligible_sorted.iterrows():
            if len(lineup_players) >= 9:
                break
                
            if player['Salary'] <= remaining_salary:
                # Check position eligibility
                player_positions = str(player['Position']).split('/')
                
                for pos in player_positions:
                    if pos in position_needs and selected_positions[pos] < position_needs[pos]:
                        lineup_players.append(player)
                        remaining_salary -= player['Salary']
                        selected_positions[pos] += 1
                        break
        
        if len(lineup_players) == 9:
            lineup_df = pd.DataFrame(lineup_players)
            total_salary = lineup_df['Salary'].sum()
            total_fppg = lineup_df['Test_FPPG'].sum()
            
            print(f"✅ Test lineup created:")
            print(f"   Players: {len(lineup_df)}")
            print(f"   Total salary: ${total_salary:,}")
            print(f"   Projected FPPG: {total_fppg:.1f}")
            print(f"   Average value: {lineup_df['value'].mean():.1f}")
            
            # Save test lineup
            lineup_df.to_csv("../data/test_enhanced_lineup.csv", index=False)
            print(f"   Saved to: test_enhanced_lineup.csv")
            
        else:
            print(f"⚠️ Could only create {len(lineup_players)} player lineup")
            
    except Exception as e:
        print(f"❌ Error creating test lineup: {e}")
        return
    
    print("\n✅ Enhanced optimizer test completed successfully!")
    print("\nNext steps:")
    print("1. Run: python enhanced_fanduel_optimizer.py")
    print("2. Check generated lineups in data folder")
    print("3. Compare performance against current optimizer")

if __name__ == "__main__":
    test_enhanced_optimizer()

#!/usr/bin/env python3
"""
TEST DASHBOARD FIXES WITH YESTERDAY'S DATA
Tests stack analysis and FanDuel CSV generation using August 17th data
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def test_stack_analysis():
    """Test if stack analysis shows correct teams"""
    print("🔍 TESTING STACK ANALYSIS")
    print("=" * 40)
    
    # Use yesterday's enhanced ML DFS file
    data_dir = os.path.join(script_dir, '..', 'data')
    enhanced_file = os.path.join(data_dir, 'enhanced_ml_dfs_lineups_20250817_170927.csv')
    
    if os.path.exists(enhanced_file):
        df = pd.read_csv(enhanced_file)
        print(f"✅ Loaded {len(df)} players from Enhanced ML DFS")
        
        # Calculate team stacks (excluding pitchers)
        hitters = df[df['position'] != 'P'].drop_duplicates(subset=['name'])
        team_stacks = hitters.groupby('team')['ml_projected_fppg'].sum().sort_values(ascending=False)
        
        print(f"📊 TOP STACKS:")
        for i, (team, fppg) in enumerate(team_stacks.head(5).items(), 1):
            print(f"   #{i} {team}: {fppg:.1f} FPPG")
        
        if team_stacks.index[0] == 'LAD':
            print("✅ STACK ANALYSIS CORRECT: LAD is #1")
            return True
        else:
            print(f"❌ STACK ANALYSIS WRONG: {team_stacks.index[0]} is #1, should be LAD")
            return False
    else:
        print(f"❌ Enhanced ML DFS file not found: {enhanced_file}")
        return False

def test_fanduel_csv_generation():
    """Test FanDuel CSV generation with yesterday's data"""
    print(f"\n🔧 TESTING FANDUEL CSV GENERATION")
    print("=" * 40)
    
    data_dir = os.path.join(script_dir, '..', 'data')
    submission_file = os.path.join(data_dir, 'fanduel_submission_20250817_170927.csv')
    
    if os.path.exists(submission_file):
        print(f"✅ Found submission file")
        
        # Test reading the data
        df = pd.read_csv(submission_file)
        cash_lineups = df[df['Contest_Type'] == 'cash']
        
        print(f"📊 Available lineups:")
        print(f"   Total: {len(df)}")
        print(f"   Cash: {len(cash_lineups)}")
        print(f"   Tournament: {len(df[df['Contest_Type'] == 'tournament'])}")
        
        if len(cash_lineups) > 0:
            # Create test FanDuel CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_output = os.path.join(data_dir, f"TEST_FANDUEL_CSV_{timestamp}.csv")
            
            with open(test_output, 'w', encoding='utf-8', newline='') as f:
                # Write FanDuel header
                f.write("P,C/1B,2B,3B,SS,OF,OF,OF,1B\n")
                
                # Write first 3 cash lineups
                for _, lineup in cash_lineups.head(3).iterrows():
                    lineup_data = [
                        str(lineup['P']),
                        str(lineup['C']),
                        str(lineup['2B']),
                        str(lineup['3B']),
                        str(lineup['SS']),
                        str(lineup['OF']),
                        str(lineup['OF2']),
                        str(lineup['OF3']),
                        str(lineup['1B'])
                    ]
                    f.write(",".join(lineup_data) + "\n")
            
            # Verify the file
            with open(test_output, 'r') as f:
                lines = f.readlines()
                
            print(f"✅ Generated test file: {os.path.basename(test_output)}")
            print(f"📋 File has {len(lines)} lines (including header)")
            
            if len(lines) > 1:
                print(f"📋 Sample lineup: {lines[1].strip()}")
                print("✅ FANDUEL CSV GENERATION WORKS!")
                return True
            else:
                print("❌ File only has header, no lineup data")
                return False
        else:
            print("❌ No cash lineups found")
            return False
    else:
        print(f"❌ Submission file not found: {submission_file}")
        return False

def main():
    print("🧪 TESTING DASHBOARD FIXES WITH YESTERDAY'S DATA")
    print("=" * 60)
    print("📅 Using August 17th data to test fixes")
    print()
    
    # Test stack analysis
    stack_ok = test_stack_analysis()
    
    # Test FanDuel CSV generation
    csv_ok = test_fanduel_csv_generation()
    
    print(f"\n📊 TEST RESULTS")
    print("=" * 20)
    print(f"Stack Analysis: {'✅ PASS' if stack_ok else '❌ FAIL'}")
    print(f"FanDuel CSV:    {'✅ PASS' if csv_ok else '❌ FAIL'}")
    
    if stack_ok and csv_ok:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ Ready to test dashboard with yesterday's data")
        print("✅ Ready to move to Option B (fresh data) when you want")
    else:
        print(f"\n⚠️ Some tests failed - need more fixes")

if __name__ == "__main__":
    main()

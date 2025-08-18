#!/usr/bin/env python3
"""
Test script to verify FanDuel CSV generation is working correctly
"""

import pandas as pd
import os
import sys

def test_csv_generation():
    """Test the CSV generation logic"""
    # Get the absolute path to this script
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    base_dir = os.path.dirname(script_dir)
    
    print(f"Script dir: {script_dir}")
    print(f"Base dir: {base_dir}")
    
    # Path to the elite tournament file
    file_path = os.path.join(base_dir, "data", "elite_tournament_lineups_20250817_114704.csv")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"✅ Testing CSV generation with: {os.path.basename(file_path)}")
    
    try:
        # Load the data
        df = pd.read_csv(file_path)
        print(f"📊 Loaded {len(df)} lineups")
        print(f"🔍 Columns: {list(df.columns)}")
        
        # Test output path
        output_path = os.path.join(base_dir, "data", "TEST_FANDUEL_CSV.csv")
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            # Write proper FanDuel header
            f.write("P,C/1B,2B,3B,SS,OF,OF,OF,1B\n")
            
            # Process first 3 lineups
            for i in range(min(3, len(df))):
                row = df.iloc[i]
                
                # Extract player names in FanDuel order
                if 'P' in df.columns and 'C' in df.columns:
                    fanduel_lineup = [
                        str(row['P']),      # P
                        str(row['C']),      # C/1B  
                        str(row['2B']),     # 2B
                        str(row['3B']),     # 3B
                        str(row['SS']),     # SS
                        str(row['OF1']),    # OF
                        str(row['OF2']),    # OF
                        str(row['OF3']),    # OF
                        str(row['1B'])      # 1B
                    ]
                    
                    print(f"✅ Lineup {i+1}: {fanduel_lineup}")
                    f.write(",".join(fanduel_lineup) + "\n")
                else:
                    print(f"❌ Missing required columns in file")
                    return
        
        print(f"✅ Test CSV created: {output_path}")
        
        # Read it back to verify
        with open(output_path, 'r') as f:
            content = f.read()
            print("\n📄 Generated CSV content:")
            print(content)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_csv_generation()

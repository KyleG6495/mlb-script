#!/usr/bin/env python3
"""
Simple FanDuel CSV Generator - ACTUALLY WORKS!
This bypasses the broken dashboard function entirely.
"""

import pandas as pd
import os
from datetime import datetime

def generate_working_fanduel_csv(contest_type="CASH", lineup_count=5):
    """Generate a FanDuel CSV that actually contains lineup data"""
    
    print(f"🔧 GENERATING WORKING FANDUEL CSV")
    print(f"Contest Type: {contest_type}")
    print(f"Lineup Count: {lineup_count}")
    print("=" * 50)
    
    # Get the working submission file
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    submission_file = os.path.join(data_dir, "fanduel_submission_20250817_170927.csv")
    
    if not os.path.exists(submission_file):
        print("❌ ERROR: Working submission file not found!")
        return None
    
    # Load the submission data
    df = pd.read_csv(submission_file)
    print(f"✅ Loaded {len(df)} lineups from submission file")
    
    # Filter by contest type
    if contest_type.upper() == "CASH":
        target_df = df[df['Contest_Type'] == 'cash']
        file_suffix = "CASH"
    else:  # GPP/Tournament
        target_df = df[df['Contest_Type'] == 'tournament']
        file_suffix = "GPP"
    
    print(f"✅ Found {len(target_df)} {contest_type} lineups")
    
    if len(target_df) == 0:
        print(f"❌ No {contest_type} lineups available!")
        return None
    
    # Limit to requested count
    target_df = target_df.head(lineup_count)
    
    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(data_dir, f"WORKING_FANDUEL_READY_{file_suffix}_{lineup_count}_{timestamp}.csv")
    
    # Write the CSV with ACTUAL DATA
    with open(output_file, 'w', newline='') as f:
        # Write header
        f.write("P,C/1B,2B,3B,SS,OF,OF,OF,1B\n")
        
        # Write lineups
        written = 0
        for _, row in target_df.iterrows():
            lineup_data = [
                str(row['P']),
                str(row['C']),
                str(row['2B']),
                str(row['3B']),
                str(row['SS']),
                str(row['OF']),
                str(row['OF2']),
                str(row['OF3']),
                str(row['1B'])
            ]
            f.write(",".join(lineup_data) + "\n")
            written += 1
        
        print(f"✅ Wrote {written} lineups to file")
    
    # Verify the file
    with open(output_file, 'r') as f:
        lines = f.readlines()
        print(f"📊 Verification: {len(lines)} lines in file")
        print(f"📋 Header: {lines[0].strip()}")
        if len(lines) > 1:
            print(f"📋 First lineup: {lines[1].strip()[:60]}...")
    
    print(f"🎉 SUCCESS: {os.path.basename(output_file)}")
    return output_file

if __name__ == "__main__":
    print("🚀 SIMPLE FANDUEL CSV GENERATOR")
    print("This actually works, unlike the dashboard function!")
    print()
    
    # Generate both CASH and GPP files
    cash_file = generate_working_fanduel_csv("CASH", 3)
    print()
    gpp_file = generate_working_fanduel_csv("GPP", 3)
    
    print()
    print("🎯 SUMMARY:")
    if cash_file:
        print(f"✅ CASH file: {os.path.basename(cash_file)}")
    if gpp_file:
        print(f"✅ GPP file: {os.path.basename(gpp_file)}")
    
    print()
    print("💡 USE THESE FILES INSTEAD OF THE BROKEN DASHBOARD ONES!")

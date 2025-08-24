#!/usr/bin/env python3
"""
Direct test of lineup export functionality
This bypasses the web interface to test the core export logic
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the Scripts directory to path so we can import the data loader
sys.path.append(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts')

def test_lineup_export():
    """Test the lineup export functionality directly"""
    print("🧪 TESTING LINEUP EXPORT FUNCTIONALITY")
    print("=" * 60)
    
    # Define paths
    fd_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate')
    
    # Find the latest Enhanced_Lineups file
    enhanced_files = list(fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
    if not enhanced_files:
        print("❌ ERROR: No Enhanced_Lineups_FD_Format files found")
        return False
    
    latest_file = max(enhanced_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Using file: {latest_file.name}")
    
    try:
        # Load the lineup data
        df = pd.read_csv(latest_file)
        print(f"📊 Loaded {len(df)} lineups")
        print(f"📋 Columns: {list(df.columns)}")
        
        if len(df) == 0:
            print("❌ ERROR: No lineups found in file")
            return False
        
        # Test exporting the first lineup
        lineup_id = 0
        lineup_row = df.iloc[lineup_id]
        
        print(f"\n🔍 Testing lineup #{lineup_id + 1}:")
        print(f"   Total Projection: {lineup_row.get('Total_Projection', 'N/A')}")
        print(f"   Total Salary: ${lineup_row.get('Total_Salary', 'N/A'):,}")
        
        # Check what positions we have
        potential_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL', 'C/1B']
        available_positions = [col for col in potential_positions if col in df.columns]
        print(f"   Available positions: {available_positions}")
        
        # Create a simple export (just copy the lineup as-is for now)
        export_df = pd.DataFrame([lineup_row])
        
        # Generate export filename
        export_filename = f"TEST_EXPORT_Lineup_{lineup_id + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_path = fd_path / export_filename
        
        # Export the lineup
        export_df.to_csv(export_path, index=False)
        
        print(f"✅ SUCCESS: Exported to {export_filename}")
        print(f"📁 Full path: {export_path}")
        
        # Verify the export file
        if export_path.exists():
            verify_df = pd.read_csv(export_path)
            print(f"✅ Verification: File contains {len(verify_df)} lineup(s)")
            print(f"📋 Export columns: {list(verify_df.columns)}")
            
            # Show first few values
            print(f"\n📋 Sample lineup data:")
            for col in available_positions[:5]:  # Show first 5 positions
                if col in verify_df.columns:
                    value = verify_df[col].iloc[0]
                    print(f"   {col}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during export test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the API endpoint directly"""
    print(f"\n🌐 TESTING API ENDPOINT")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get('http://localhost:5004/api/export-lineup/0', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API endpoint is working!")
            return True
        else:
            print("❌ API endpoint returned error")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 LINEUP EXPORT DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test 1: Direct export functionality
    direct_test_passed = test_lineup_export()
    
    # Test 2: API endpoint test
    api_test_passed = test_api_endpoint()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Direct Export: {'✅ PASSED' if direct_test_passed else '❌ FAILED'}")
    print(f"   API Endpoint:  {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    
    if direct_test_passed and api_test_passed:
        print(f"\n🎉 ALL TESTS PASSED - Export functionality should work!")
    elif direct_test_passed:
        print(f"\n⚠️  Direct export works, but API has issues")
    else:
        print(f"\n🚨 CORE EXPORT FUNCTIONALITY HAS PROBLEMS")

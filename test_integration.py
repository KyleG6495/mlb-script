#!/usr/bin/env python3
"""
Simple test to verify the scraper integration works
"""
import os
import pandas as pd
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_integration():
    """Test that our scrapers work and data loads correctly"""
    
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    python_exe = r"C:\Users\kgone\AppData\Local\Programs\Python\Python311\python.exe"
    
    print(" TESTING SCRAPER INTEGRATION...")
    print("=" * 50)
    
    # Test 1: Check if Underdog data exists
    print("\n1 Testing Underdog data loading...")
    ud_excel = os.path.join(data_dir, "uf_mlb_picks.xlsx")
    ud_csv = os.path.join(data_dir, "today_pitcher_props_2025-07-26.csv")
    
    if os.path.exists(ud_excel):
        df = pd.read_excel(ud_excel)
        print(f"SUCCESS: Underdog Excel loaded: {len(df)} players, {len(df.columns)-2} stat types")
        print(f"   Sample players: {list(df['player_name'].head(3))}")
        print(f"   Sample stats: {[col for col in df.columns if col not in ['player_name', 'source']][:5]}")
    else:
        print(f"ERROR: Underdog Excel not found: {ud_excel}")
    
    if os.path.exists(ud_csv):
        df_csv = pd.read_csv(ud_csv)
        print(f"SUCCESS: Underdog CSV loaded: {len(df_csv)} prop lines")
        print(f"   Sample props: {df_csv[['player_name', 'stat_type', 'line']].head(3).to_string(index=False)}")
    else:
        print(f"ERROR: Underdog CSV not found: {ud_csv}")
    
    # Test 2: Check if PrizePicks data exists
    print("\n2 Testing PrizePicks data loading...")
    pp_files = [f for f in os.listdir(data_dir) if f.startswith('PP_mlb_picks_') and f.endswith('.xlsx')]
    if pp_files:
        pp_file = max(pp_files, key=lambda x: x)  # Get most recent
        pp_path = os.path.join(data_dir, pp_file)
        df_pp = pd.read_excel(pp_path)
        print(f"SUCCESS: PrizePicks loaded: {len(df_pp)} players from {pp_file}")
        print(f"   Sample players: {list(df_pp['player_name'].head(3))}")
        print(f"   Sample stats: {[col for col in df_pp.columns if col != 'player_name'][:5]}")
    else:
        print("ERROR: No PrizePicks files found")
    
    # Test 3: Test data conversion (like automated system does)
    print("\n3 Testing data conversion...")
    if os.path.exists(ud_excel):
        df = pd.read_excel(ud_excel)
        # Convert to long format like the automated system
        df_long = pd.melt(df, id_vars=['player_name'], value_name='line').dropna(subset=['line'])
        df_long['source'] = 'Underdog'
        print(f"SUCCESS: Underdog conversion: {len(df_long)} prop lines after melting")
        
        # Show sample of converted data
        print("   Sample converted data:")
        print(f"   {df_long[['player_name', 'variable', 'line', 'source']].head(5).to_string(index=False)}")
    
    if pp_files:
        df_pp = pd.read_excel(pp_path)
        df_pp_long = pd.melt(df_pp, id_vars=['player_name'], value_name='line').dropna(subset=['line'])
        df_pp_long['source'] = 'PrizePicks'
        print(f"SUCCESS: PrizePicks conversion: {len(df_pp_long)} prop lines after melting")
        
        # Show sample of converted data
        print("   Sample converted data:")
        print(f"   {df_pp_long[['player_name', 'variable', 'line', 'source']].head(5).to_string(index=False)}")
    
    print("\nTARGET: INTEGRATION TEST COMPLETE!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_integration()

#!/usr/bin/env python3
"""
PrizePicks Excel to CSV Converter

Converts the PrizePicks Excel files to readable CSV format.
"""

import pandas as pd
import os
import glob
from datetime import datetime

def convert_prizepicks_to_csv():
    """Convert PrizePicks Excel files to CSV format"""
    
    print("SWAP: PRIZEPICKS EXCEL TO CSV CONVERTER")
    print("=" * 40)
    
    # Look for the main PrizePicks file
    main_file = "../data/PrizePicks_MLB.xlsx"
    
    if os.path.exists(main_file):
        print(f"SUCCESS: Found main PrizePicks file: {main_file}")
        
        try:
            # Read the Excel file
            df = pd.read_excel(main_file)
            print(f"DATA: Loaded {len(df)} props from PrizePicks")
            
            # Show column structure
            print(f"INFO: Columns: {list(df.columns)}")
            
            # Save as CSV
            csv_path = "../data/prizepicks_mlb.csv"
            df.to_csv(csv_path, index=False)
            print(f"SUCCESS: Saved as CSV: {csv_path}")
            
            # Show sample data
            print(f"\n Sample data:")
            print(df.head().to_string())
            
            # Show stats
            if 'player_name' in df.columns:
                print(f"\nPROGRESS: Stats:")
                print(f"    Unique players: {df['player_name'].nunique()}")
                
                # Count stat types
                stat_cols = [col for col in df.columns if col not in ['player_name', 'team', 'position']]
                prop_counts = []
                for col in stat_cols:
                    non_null = df[col].notna().sum()
                    if non_null > 0:
                        prop_counts.append((col, non_null))
                
                prop_counts.sort(key=lambda x: x[1], reverse=True)
                print(f"    Prop types:")
                for prop, count in prop_counts[:10]:  # Top 10
                    print(f"     - {prop}: {count} props")
            
            return csv_path
            
        except Exception as e:
            print(f"ERROR: Error reading Excel file: {e}")
            return None
    
    else:
        print(f"ERROR: Main PrizePicks file not found: {main_file}")
        
        # Look for dated files
        dated_files = glob.glob("../data/PP_mlb_picks_*.xlsx")
        if dated_files:
            # Get the most recent file
            latest_file = max(dated_files, key=os.path.getmtime)
            print(f"SUCCESS: Found latest dated file: {latest_file}")
            
            try:
                df = pd.read_excel(latest_file)
                print(f"DATA: Loaded {len(df)} props from latest file")
                
                # Save as CSV
                csv_path = "../data/prizepicks_mlb_latest.csv"
                df.to_csv(csv_path, index=False)
                print(f"SUCCESS: Saved as CSV: {csv_path}")
                
                return csv_path
                
            except Exception as e:
                print(f"ERROR: Error reading latest file: {e}")
                return None
        else:
            print("ERROR: No PrizePicks files found!")
            return None

def show_available_props(csv_path):
    """Show available prop types and sample data"""
    
    if not csv_path:
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        print(f"\nTARGET: PRIZEPICKS PROP ANALYSIS")
        print("=" * 40)
        
        # Show player sample
        if 'player_name' in df.columns:
            print(f" Sample players:")
            for player in df['player_name'].unique()[:5]:
                print(f"    {player}")
        
        # Show available prop types with lines
        print(f"\nDATA: Available Props:")
        stat_cols = [col for col in df.columns if col not in ['player_name', 'team', 'position']]
        
        for col in stat_cols:
            non_null_data = df[df[col].notna()]
            if len(non_null_data) > 0:
                min_line = non_null_data[col].min()
                max_line = non_null_data[col].max()
                count = len(non_null_data)
                print(f"    {col}: {count} props (lines: {min_line} - {max_line})")
        
        # Show sample props for first few players
        print(f"\nINFO: Sample Props:")
        for _, player_row in df.head(3).iterrows():
            if 'player_name' in player_row:
                print(f"\n   {player_row['player_name']}:")
                for col in stat_cols:
                    if pd.notna(player_row[col]):
                        print(f"     - {col}: {player_row[col]}")
        
    except Exception as e:
        print(f"ERROR: Error analyzing CSV: {e}")

if __name__ == "__main__":
    csv_path = convert_prizepicks_to_csv()
    show_available_props(csv_path)

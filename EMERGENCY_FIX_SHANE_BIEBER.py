#!/usr/bin/env python3
"""
EMERGENCY FIX - Remove Shane Bieber from pitcher data
"""
import pandas as pd
import os

def fix_pitcher_data():
    """Remove Shane Bieber from pitcher features"""
    
    file_path = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_pitcher_features_final.csv"
    backup_path = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_pitcher_features_final_BACKUP_SHANE_BIEBER.csv"
    
    # Create backup
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.to_csv(backup_path, index=False)
        print(f"✅ Created backup: {backup_path}")
        
        # Check Shane Bieber entries
        bieber_rows = df[df['Nickname'].str.lower().str.contains('bieber', na=False)]
        print(f"🚨 Found {len(bieber_rows)} Shane Bieber rows")
        
        if len(bieber_rows) > 0:
            print("Shane Bieber entries:")
            for i, row in bieber_rows.iterrows():
                print(f"  Row {i}: {row['First Name']} {row['Last Name']} - {row['FPPG']} FPPG, ${row['Salary']}, Status: {row.get('IL', 'Active')}")
        
        # Remove Shane Bieber
        df_clean = df[~df['Nickname'].str.lower().str.contains('bieber', na=False)]
        
        print(f"📊 Before: {len(df)} pitchers")
        print(f"📊 After:  {len(df_clean)} pitchers")
        print(f"🗑️  Removed: {len(df) - len(df_clean)} Shane Bieber entries")
        
        # Save cleaned data
        df_clean.to_csv(file_path, index=False)
        print(f"✅ Saved cleaned data back to: {file_path}")
        print("🚨 Shane Bieber completely removed from pitcher data!")
        
        return True
    else:
        print(f"❌ File not found: {file_path}")
        return False

if __name__ == "__main__":
    fix_pitcher_data()

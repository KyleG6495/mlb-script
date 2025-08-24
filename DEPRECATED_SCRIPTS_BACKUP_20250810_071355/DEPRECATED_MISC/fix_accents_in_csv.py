#!/usr/bin/env python3
"""
FIX ACCENTS IN CSV FILES
========================
Removes accents from player names in existing CSV files to fix encoding issues.
"""

import pandas as pd
import unicodedata
from pathlib import Path

def remove_accents(text):
    """Remove accents and special characters from text"""
    if not text or pd.isna(text):
        return text
    # Normalize to NFD (decomposed form) and filter out combining characters
    normalized = unicodedata.normalize('NFD', str(text))
    ascii_text = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    return ascii_text

def fix_csv_accents(input_file, output_file=None):
    """Fix accents in a CSV file"""
    print(f"🔧 Fixing accents in: {input_file}")
    
    # Read the CSV file
    try:
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(input_file, encoding=encoding)
                print(f"✅ Successfully read with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        else:
            print("❌ Could not read file with any encoding")
            return
            
        # Fix the 'name' column if it exists
        if 'name' in df.columns:
            print(f"📝 Processing {len(df)} player names...")
            
            # Show examples before fixing
            problematic_names = df[df['name'].str.contains('Ã|á|é|í|ó|ú|ñ|ü', na=False)]['name'].head(5)
            if not problematic_names.empty:
                print("🔍 Examples of names with accents:")
                for name in problematic_names:
                    fixed_name = remove_accents(name)
                    print(f"  '{name}' → '{fixed_name}'")
            
            # Apply accent removal
            df['name'] = df['name'].apply(remove_accents)
            
            # Count fixed names
            fixed_count = len(df[df['name'].str.contains('[a-zA-Z]', na=False)])
            print(f"✅ Fixed {fixed_count} player names")
        else:
            print("⚠️ No 'name' column found in CSV")
            
        # Save the fixed file
        if output_file is None:
            output_file = input_file  # Overwrite original
            
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Saved fixed file: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return False

def main():
    """Main execution function"""
    print("🔧 ACCENT FIXER FOR CSV FILES")
    print("=" * 40)
    
    # Fix the main actual results file
    data_dir = Path(__file__).resolve().parent.parent / "data"
    
    files_to_fix = [
        "actual_results_latest.csv",
        "actual_results_20250724.csv"
    ]
    
    for filename in files_to_fix:
        file_path = data_dir / filename
        if file_path.exists():
            print(f"\n📁 Processing: {filename}")
            success = fix_csv_accents(file_path)
            if success:
                print(f"✅ {filename} fixed successfully!")
            else:
                print(f"❌ Failed to fix {filename}")
        else:
            print(f"⚠️ File not found: {filename}")
    
    print("\n🎉 Accent fixing complete!")
    print("📝 All player names should now display properly without encoding issues.")

if __name__ == "__main__":
    main()

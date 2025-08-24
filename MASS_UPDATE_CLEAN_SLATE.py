#!/usr/bin/env python3
"""
MASS UPDATE SCRIPT - Replace all fd_slate_today.csv references with clean slate priority
"""

import os
import re
import glob

def update_file_with_clean_slate(file_path):
    """Update a single file to prioritize clean slate data"""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Simple path replacements
        patterns = [
            # Replace direct references
            (r'fd_slate_today\.csv', 'fd_slate_today_clean.csv'),
            
            # Update load statements to check for clean version first
            (r'pd\.read_csv\(["\']([^"\']*fd_slate_today)\.csv["\']\)', 
             r'pd.read_csv("\1_clean.csv" if os.path.exists("\1_clean.csv") else "\1.csv")'),
            
            # Update path variables
            (r'SLATE_PATH\s*=\s*["\']([^"\']*fd_slate_today)\.csv["\']',
             r'SLATE_PATH = "\1_clean.csv" if os.path.exists("\1_clean.csv") else "\1.csv"'),
            
            (r'SLATE_FILE\s*=\s*["\']([^"\']*fd_slate_today)\.csv["\']',
             r'SLATE_FILE = "\1_clean.csv" if os.path.exists("\1_clean.csv") else "\1.csv"'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            # Create backup
            backup_path = file_path + '.backup_clean'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Updated: {file_path}")
            print(f"  💾 Backup: {backup_path}")
            return True
        else:
            print(f"  ⏭️ No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def main():
    """Update all Python scripts to use clean slate data"""
    print("🧹 MASS CLEAN SLATE UPDATE")
    print("="*50)
    
    # Find all Python files that might reference the slate
    script_dir = "."
    patterns = ["*.py", "DAILY_RUNNERS/*.bat"]
    
    files_to_update = []
    for pattern in patterns:
        files_to_update.extend(glob.glob(pattern, recursive=True))
    
    # Filter to files that actually contain fd_slate_today
    relevant_files = []
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if 'fd_slate_today.csv' in f.read():
                    relevant_files.append(file_path)
        except:
            continue
    
    print(f"Found {len(relevant_files)} files to update:")
    
    updated_count = 0
    for file_path in relevant_files:
        if update_file_with_clean_slate(file_path):
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} of {len(relevant_files)} files")
    print("🎯 All scripts now prioritize clean slate data!")

if __name__ == "__main__":
    main()

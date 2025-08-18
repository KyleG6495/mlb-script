#!/usr/bin/env python3
"""
UNICODE FIXER
=============
Fixes all Unicode encoding issues in DFS scripts
"""

import os
import re
import glob

def fix_unicode_in_file(file_path):
    """Fix Unicode issues in a single file"""
    try:
        # Read file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove problematic Unicode characters
        # Replace emoji patterns with simple text
        replacements = {
            r'\\U0001f\w{3}': '',  # Remove Unicode emoji patterns
            r'TIME:': 'TIME:',
            r'DATA:': 'DATA:',
            r'SUCCESS:': 'SUCCESS:',
            r'ERROR:': 'ERROR:',
            r'STEP:': 'STEP:',
            r'LINEUP:': 'LINEUP:',
            r'INFO:': 'INFO:',
            r'TARGET:': 'TARGET:',
            r'START:': 'START:',
            r'BASEBALL:': 'BASEBALL:',
            r'FILTER:': 'FILTER:',
            r'OWNERSHIP:': 'OWNERSHIP:',
            r'SWAP:': 'SWAP:',
            r'MONEY:': 'MONEY:',
            r'PROGRESS:': 'PROGRESS:',
            r'COMPLETE:': 'COMPLETE:',
            r'WARNING:': 'WARNING:',
            r'TIP:': 'TIP:',
        }
        
        changed = False
        for pattern, replacement in replacements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changed = True
        
        # Also remove any other Unicode characters that might cause issues
        # Keep only ASCII characters and basic symbols
        content = content.encode('ascii', 'ignore').decode('ascii')
        
        if changed:
            # Write back with UTF-8 encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Unicode issues in: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def fix_all_unicode_issues():
    """Fix Unicode issues in all Python scripts"""
    
    print("UNICODE FIXER - Removing problematic characters from DFS scripts")
    print("=" * 70)
    
    # Get all Python files in the Scripts directory
    script_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
    python_files = glob.glob(os.path.join(script_dir, "*.py"))
    
    fixed_count = 0
    
    for file_path in python_files:
        if fix_unicode_in_file(file_path):
            fixed_count += 1
    
    print(f"\nSUCCESS: Fixed Unicode issues in {fixed_count} files")
    print("Your DFS scripts should now run without encoding errors!")

if __name__ == "__main__":
    fix_all_unicode_issues()

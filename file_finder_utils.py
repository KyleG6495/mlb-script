#!/usr/bin/env python3
"""
File Finder Utilities
Simple utilities for finding and reading CSV files safely
"""

import pandas as pd
import os
import glob
from datetime import datetime

def safe_read_csv(file_path, **kwargs):
    """
    Safely read a CSV file with error handling
    
    Args:
        file_path (str): Path to the CSV file
        **kwargs: Additional arguments for pd.read_csv()
    
    Returns:
        pandas.DataFrame or None: DataFrame if successful, None if error
    """
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            return None
            
        # Default encoding handling
        encoding = kwargs.get('encoding', 'utf-8')
        
        # Try different encodings if needed
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252']
        
        for enc in encodings_to_try:
            try:
                kwargs['encoding'] = enc
                df = pd.read_csv(file_path, **kwargs)
                print(f"✅ Loaded {file_path} with {enc} encoding: {len(df)} rows")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if enc == encodings_to_try[-1]:  # Last attempt
                    print(f"❌ Error reading {file_path}: {e}")
                    return None
                continue
                
        print(f"❌ Could not read {file_path} with any encoding")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error reading {file_path}: {e}")
        return None

def find_latest_file(directory, pattern):
    """
    Find the most recent file matching a pattern
    
    Args:
        directory (str): Directory to search
        pattern (str): File pattern (glob style)
    
    Returns:
        str or None: Path to latest file, None if not found
    """
    try:
        if not os.path.exists(directory):
            print(f"⚠️ Directory not found: {directory}")
            return None
            
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)
        
        if not files:
            print(f"⚠️ No files found matching: {search_pattern}")
            return None
            
        # Sort by modification time, newest first
        latest_file = max(files, key=os.path.getmtime)
        print(f"📁 Found latest file: {os.path.basename(latest_file)}")
        return latest_file
        
    except Exception as e:
        print(f"❌ Error finding files: {e}")
        return None

def find_files_by_keywords(directory, keywords, extension='.csv'):
    """
    Find files containing specific keywords
    
    Args:
        directory (str): Directory to search
        keywords (list): List of keywords to search for
        extension (str): File extension filter
    
    Returns:
        list: List of matching file paths
    """
    try:
        if not os.path.exists(directory):
            print(f"⚠️ Directory not found: {directory}")
            return []
            
        matching_files = []
        
        for file in os.listdir(directory):
            if file.endswith(extension):
                file_lower = file.lower()
                if any(keyword.lower() in file_lower for keyword in keywords):
                    matching_files.append(os.path.join(directory, file))
        
        # Sort by modification time, newest first
        matching_files.sort(key=os.path.getmtime, reverse=True)
        
        print(f"📁 Found {len(matching_files)} files with keywords {keywords}")
        return matching_files
        
    except Exception as e:
        print(f"❌ Error searching files: {e}")
        return []

def get_file_info(file_path):
    """
    Get file information
    
    Args:
        file_path (str): Path to file
    
    Returns:
        dict: File information
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"❌ Error getting file info: {e}")
        return None

# Test function
if __name__ == "__main__":
    print("🔧 Testing file_finder_utils...")
    
    # Test directory
    test_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    
    if os.path.exists(test_dir):
        print(f"📁 Testing in directory: {test_dir}")
        
        # Test finding files by keywords
        ownership_files = find_files_by_keywords(test_dir, ['ownership'])
        print(f"Found {len(ownership_files)} ownership files")
        
        # Test reading a file if found
        if ownership_files:
            df = safe_read_csv(ownership_files[0])
            if df is not None:
                print(f"Successfully read file with {len(df)} rows")
    else:
        print(f"❌ Test directory not found: {test_dir}")
    
    print("✅ file_finder_utils test complete")

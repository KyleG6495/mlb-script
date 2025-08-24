#!/usr/bin/env python3
"""
Utility function to get clean slate path - use this in all scripts
"""

import os
import pandas as pd

def get_clean_slate_path(base_dir="../fd_current_slate"):
    """
    Get path to clean slate data, falling back to original if not available
    Returns: (path, is_clean)
    """
    clean_path = f"{base_dir}/fd_slate_today_clean.csv"
    original_path = f"{base_dir}/fd_slate_today.csv"
    
    if os.path.exists(clean_path):
        return clean_path, True
    elif os.path.exists(original_path):
        return original_path, False
    else:
        raise FileNotFoundError("No slate file found (clean or original)")

def load_clean_slate(base_dir="../fd_current_slate"):
    """
    Load the cleanest available slate data
    """
    path, is_clean = get_clean_slate_path(base_dir)
    df = pd.read_csv(path)
    
    status = "clean" if is_clean else "original (may include injured players)"
    print(f"📊 Loaded {status} slate: {len(df)} players from {os.path.basename(path)}")
    
    return df, is_clean

if __name__ == "__main__":
    # Test the function
    try:
        df, is_clean = load_clean_slate()
        print(f"✅ Successfully loaded {'clean' if is_clean else 'original'} slate with {len(df)} players")
    except Exception as e:
        print(f"❌ Error: {e}")

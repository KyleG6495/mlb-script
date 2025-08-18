#!/usr/bin/env python3
"""
FILE FINDER UTILITIES
Dynamic file discovery to eliminate hardcoded dates
"""

import os
import glob
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_most_recent_file(pattern, data_dir="../data"):
    """
    Find the most recent file matching a pattern
    
    Args:
        pattern: Glob pattern to match (e.g., "enhanced_projections_*.csv")
        data_dir: Directory to search in
    
    Returns:
        str: Path to most recent file or None if not found
    """
    try:
        search_pattern = os.path.join(data_dir, pattern)
        files = glob.glob(search_pattern)
        
        if not files:
            logger.warning(f"No files found matching pattern: {pattern}")
            return None
        
        # Sort by modification time, most recent first
        files.sort(key=os.path.getmtime, reverse=True)
        most_recent = files[0]
        
        logger.info(f"Found most recent file: {os.path.basename(most_recent)}")
        return most_recent
    
    except Exception as e:
        logger.error(f"Error finding files with pattern {pattern}: {e}")
        return None

def get_today_slate_file(slate_dir="../fd_current_slate"):
    """
    Get today's FanDuel slate file
    Prioritizes fd_slate_today.csv, falls back to most recent
    """
    try:
        # First try today's slate
        today_file = os.path.join(slate_dir, "fd_slate_today.csv")
        if os.path.exists(today_file):
            logger.info("✅ Using today's slate: fd_slate_today.csv")
            return today_file
        
        # Fall back to most recent slate file
        pattern = os.path.join(slate_dir, "*.csv")
        files = glob.glob(pattern)
        
        if not files:
            logger.warning("No slate files found")
            return None
        
        files.sort(key=os.path.getmtime, reverse=True)
        most_recent = files[0]
        
        logger.warning(f"No fd_slate_today.csv found, using: {os.path.basename(most_recent)}")
        return most_recent
    
    except Exception as e:
        logger.error(f"Error finding slate file: {e}")
        return None

def get_data_files():
    """
    Get the most recent data files for projections, ownership, etc.
    
    Returns:
        dict: Dictionary of file paths by type
    """
    files = {}
    
    # Get today's slate first
    files['slate'] = get_today_slate_file()
    
    # Get most recent projections
    files['projections'] = get_most_recent_file("enhanced_projections_*.csv")
    
    # Get most recent ownership
    files['ownership'] = get_most_recent_file("advanced_ownership_projections_*.csv")
    
    # Get most recent actual results
    files['results'] = get_most_recent_file("actual_results_*.csv")
    
    # Get most recent lineups
    files['lineups'] = get_most_recent_file("enhanced_ml_dfs_lineups_*.csv")
    files['elite_lineups'] = get_most_recent_file("elite_tournament_lineups_*.csv")
    files['ceiling_lineups'] = get_most_recent_file("enhanced_ceiling_lineups_*.csv")
    
    # Get most recent weather data
    files['weather'] = get_most_recent_file("real_weather_enhanced_*.csv")
    files['weather_park'] = get_most_recent_file("weather_park_enhanced_*.csv")
    files['weather_projections'] = get_most_recent_file("weather_enhanced_projections_*.csv")
    
    # Get FanDuel ready files
    files['fanduel_ready'] = get_most_recent_file("FANDUEL_READY_ELITE_LINEUPS_*.csv")
    files['ultimate_lineups'] = get_most_recent_file("ULTIMATE_FANDUEL_LINEUPS_*.csv")
    files['ultimate_summary'] = get_most_recent_file("ULTIMATE_FANDUEL_SUMMARY_*.csv")
    
    # Filter out None values
    files = {k: v for k, v in files.items() if v is not None}
    
    logger.info(f"📁 Found {len(files)} data files")
    for file_type, file_path in files.items():
        logger.info(f"  {file_type}: {os.path.basename(file_path)}")
    
    return files

def validate_file_freshness(file_path, max_age_hours=24):
    """
    Check if a file is fresh enough for use
    
    Args:
        file_path: Path to file
        max_age_hours: Maximum age in hours
    
    Returns:
        bool: True if file is fresh enough
    """
    if not file_path or not os.path.exists(file_path):
        return False
    
    try:
        file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))).total_seconds() / 3600
        is_fresh = file_age <= max_age_hours
        
        if not is_fresh:
            logger.warning(f"File {os.path.basename(file_path)} is {file_age:.1f} hours old (max: {max_age_hours})")
        
        return is_fresh
    
    except Exception as e:
        logger.error(f"Error checking file freshness: {e}")
        return False

def safe_read_csv(file_path, fallback_files=None):
    """
    Safely read a CSV file with fallback options
    
    Args:
        file_path: Primary file to read
        fallback_files: List of fallback files to try
    
    Returns:
        pd.DataFrame or None
    """
    files_to_try = [file_path]
    if fallback_files:
        files_to_try.extend(fallback_files)
    
    for file in files_to_try:
        if file and os.path.exists(file):
            try:
                df = pd.read_csv(file)
                logger.info(f"✅ Successfully loaded: {os.path.basename(file)} ({len(df)} rows)")
                return df
            except Exception as e:
                logger.warning(f"Failed to read {file}: {e}")
                continue
    
    logger.error("Failed to read any files")
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 DYNAMIC FILE DISCOVERY")
    print("=" * 50)
    
    # Test the file finder
    files = get_data_files()
    
    print(f"\n📊 FOUND {len(files)} FILES:")
    for file_type, file_path in files.items():
        file_name = os.path.basename(file_path)
        file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))).total_seconds() / 3600
        print(f"  {file_type:20}: {file_name} ({file_age:.1f}h old)")

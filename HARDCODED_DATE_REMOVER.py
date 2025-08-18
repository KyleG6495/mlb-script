#!/usr/bin/env python3
"""
HARDCODED DATE REMOVER
Updates all scripts to use dynamic file discovery instead of hardcoded dates
"""

import os
import re
import glob
import logging
from file_finder_utils import get_data_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_script_imports(script_path):
    """Add file_finder_utils import to a script if not present"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if import already exists
        if 'from file_finder_utils import' in content or 'import file_finder_utils' in content:
            return False, "Import already exists"
        
        # Find import section and add our import
        import_pattern = r'(import pandas as pd\nimport numpy as np)'
        replacement = r'\1\nfrom file_finder_utils import get_data_files, safe_read_csv'
        
        updated_content = re.sub(import_pattern, replacement, content)
        
        if updated_content != content:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True, "Added import"
        
        return False, "No pandas import found"
    
    except Exception as e:
        return False, f"Error: {e}"

def remove_hardcoded_dates_from_script(script_path):
    """Remove hardcoded dates from a single script"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updates = []
        
        # Pattern 1: Direct CSV file references with dates
        date_patterns = [
            # Enhanced projections
            (r'enhanced_projections_\d{8}_\d{6}\.csv', 'get_data_files()[\"projections\"]'),
            # Ownership projections  
            (r'advanced_ownership_projections_\d{8}_\d{6}\.csv', 'get_data_files()[\"ownership\"]'),
            # Results files
            (r'actual_results_\d{8}\.csv', 'get_data_files()[\"results\"]'),
            # Lineup files
            (r'enhanced_ml_dfs_lineups_\d{8}_\d{6}\.csv', 'get_data_files()[\"lineups\"]'),
            (r'elite_tournament_lineups_\d{8}_\d{6}\.csv', 'get_data_files()[\"elite_lineups\"]'),
            (r'enhanced_ceiling_lineups_\d{8}_\d{6}\.csv', 'get_data_files()[\"ceiling_lineups\"]'),
            # Weather files
            (r'real_weather_enhanced_\d{8}_\d{6}\.csv', 'get_data_files()[\"weather\"]'),
            (r'weather_park_enhanced_\d{8}_\d{6}\.csv', 'get_data_files()[\"weather_park\"]'),
            (r'weather_enhanced_projections_\d{8}_\d{6}\.csv', 'get_data_files()[\"weather_projections\"]'),
            # FanDuel files
            (r'FANDUEL_READY_ELITE_LINEUPS_\d{8}\.csv', 'get_data_files()[\"fanduel_ready\"]'),
            (r'ULTIMATE_FANDUEL_LINEUPS_\d{8}_\d{6}\.csv', 'get_data_files()[\"ultimate_lineups\"]'),
            (r'ULTIMATE_FANDUEL_SUMMARY_\d{8}_\d{6}\.csv', 'get_data_files()[\"ultimate_summary\"]'),
        ]
        
        for pattern, replacement in date_patterns:
            # Find all matches
            matches = re.findall(pattern, content)
            if matches:
                # Replace file path construction
                content = re.sub(
                    rf'["\']([^"\']*/{pattern})["\']',
                    f'{replacement}',
                    content
                )
                updates.append(f"Replaced {len(matches)} instances of {pattern}")
        
        # Additional specific replacements for common patterns
        replacements = [
            # Direct file assignments
            (r'projections_file = "[^"]*enhanced_projections_\d{8}_\d{6}\.csv"', 
             'projections_file = get_data_files()["projections"]'),
            (r'ownership_file = "[^"]*advanced_ownership_projections_\d{8}_\d{6}\.csv"', 
             'ownership_file = get_data_files()["ownership"]'),
            (r'lineup_file = "[^"]*enhanced_ml_dfs_lineups_\d{8}_\d{6}\.csv"', 
             'lineup_file = get_data_files()["lineups"]'),
            # Timestamp hardcoding
            (r'timestamp = "\d{8}_\d{6}"', 
             'timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")'),
        ]
        
        for pattern, replacement in replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updates.append(f"Updated assignment pattern")
        
        # Write back if changes were made
        if content != original_content:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, updates
        
        return False, ["No hardcoded dates found"]
    
    except Exception as e:
        return False, [f"Error: {e}"]

def update_all_scripts():
    """Update all Python scripts in the Scripts directory"""
    scripts_dir = "."
    script_files = glob.glob(os.path.join(scripts_dir, "*.py"))
    
    # Exclude utility files
    exclude_files = ["file_finder_utils.py", "HARDCODED_DATE_REMOVER.py"]
    script_files = [f for f in script_files if os.path.basename(f) not in exclude_files]
    
    logger.info(f"🔧 Found {len(script_files)} scripts to update")
    
    updated_files = []
    failed_files = []
    
    for script_path in script_files:
        script_name = os.path.basename(script_path)
        logger.info(f"Processing: {script_name}")
        
        try:
            # Add imports if needed
            import_success, import_msg = update_script_imports(script_path)
            
            # Remove hardcoded dates
            update_success, update_msgs = remove_hardcoded_dates_from_script(script_path)
            
            if import_success or update_success:
                updated_files.append(script_name)
                logger.info(f"  ✅ Updated: {script_name}")
                if import_success:
                    logger.info(f"    📦 {import_msg}")
                for msg in update_msgs:
                    logger.info(f"    🔄 {msg}")
            else:
                logger.info(f"  ⏭️  No updates needed: {script_name}")
        
        except Exception as e:
            failed_files.append((script_name, str(e)))
            logger.error(f"  ❌ Failed: {script_name} - {e}")
    
    # Summary
    logger.info(f"\n📊 UPDATE SUMMARY:")
    logger.info(f"  ✅ Updated: {len(updated_files)} files")
    logger.info(f"  ❌ Failed: {len(failed_files)} files")
    logger.info(f"  ⏭️  Skipped: {len(script_files) - len(updated_files) - len(failed_files)} files")
    
    if updated_files:
        logger.info(f"\n🔄 UPDATED FILES:")
        for file in updated_files:
            logger.info(f"  - {file}")
    
    if failed_files:
        logger.info(f"\n❌ FAILED FILES:")
        for file, error in failed_files:
            logger.info(f"  - {file}: {error}")

if __name__ == "__main__":
    print("🚀 HARDCODED DATE REMOVER")
    print("=" * 50)
    
    update_all_scripts()
    
    print("\n✅ Date removal complete!")
    print("🎯 All scripts now use dynamic file discovery")

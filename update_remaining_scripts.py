#!/usr/bin/env python3
"""
SCRIPT UPDATER FOR STARTING LINEUPS MASTER FILE
===============================================
Updates remaining scripts to use fd_slate_starters_only.csv instead of fd_slate_today.csv
"""

import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_script_references():
    """Update remaining scripts to use the starters-only file"""
    
    # Key scripts that should use starters-only file
    priority_scripts = [
        "WINNING_LINEUP_BUILDER.py",
        "REAL_PLAYERS_LINEUP_BUILDER.py",
        "SALARY_CAP_REAL_LINEUP_BUILDER.py",
        "CHAMPIONSHIP_LINEUP_BUILDER.py",
        "MULTIPLE_CHAMPIONSHIP_BUILDER.py",
        "SIMPLE_CLEAN_GENERATOR.py"
    ]
    
    logger.info("SWAP: UPDATING REMAINING SCRIPTS TO USE STARTING LINEUPS MASTER FILE")
    logger.info("=" * 70)
    
    updated_count = 0
    
    for script in priority_scripts:
        script_path = f"./{script}"
        
        if os.path.exists(script_path):
            logger.info(f" Processing: {script}")
            
            # Read the file
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Track if we made changes
                original_content = content
                
                # Replace common patterns
                replacements = [
                    ('pd.read_csv(\'../fd_current_slate/fd_slate_today.csv\')', 
                     'pd.read_csv(\'../data/fd_slate_starters_only.csv\')'),
                    ('pd.read_csv("../fd_current_slate/fd_slate_today.csv")', 
                     'pd.read_csv("../data/fd_slate_starters_only.csv")'),
                    ('pd.read_csv(\'../data/fd_slate_today.csv\')', 
                     'pd.read_csv(\'../data/fd_slate_starters_only.csv\')'),
                    ('pd.read_csv("../data/fd_slate_today.csv")', 
                     'pd.read_csv("../data/fd_slate_starters_only.csv")'),
                    ('fd_slate_today.csv', 'fd_slate_starters_only.csv')
                ]
                
                for old, new in replacements:
                    if old in content:
                        content = content.replace(old, new)
                        logger.info(f"   SUCCESS: Updated: {old} -> {new}")
                
                # Write back if changed
                if content != original_content:
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"    Saved updated {script}")
                    updated_count += 1
                else:
                    logger.info(f"    No changes needed for {script}")
                
            except Exception as e:
                logger.error(f"   ERROR: Error processing {script}: {str(e)}")
        else:
            logger.warning(f"   WARNING: Script not found: {script}")
    
    logger.info("=" * 70)
    logger.info(f"COMPLETE: SCRIPT UPDATE COMPLETE!")
    logger.info(f"DATA: Updated {updated_count} scripts to use starters-only file")
    logger.info("")
    logger.info("TIP: BENEFITS OF USING STARTERS-ONLY FILE:")
    logger.info("   SUCCESS: No more Drake Baldwin or bench players in lineups")
    logger.info("   SUCCESS: No complex batting order filtering needed")
    logger.info("   SUCCESS: Pre-validated starting lineups only")
    logger.info("   SUCCESS: Consistent across all scripts")
    logger.info("   SUCCESS: 90 confirmed starters vs 524 total players")

if __name__ == "__main__":
    update_script_references()

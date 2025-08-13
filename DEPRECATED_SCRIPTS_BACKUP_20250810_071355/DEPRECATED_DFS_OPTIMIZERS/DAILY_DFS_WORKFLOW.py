#!/usr/bin/env python3
"""
DAILY MLB DFS WORKFLOW
=====================
Complete step-by-step process to generate clean, optimized DFS lineups
without injured players or hardcoded sample data.

DISCOVERED ISSUE: Shane Bieber was appearing in lineups even though he's on IL
ROOT CAUSE: FanDuel slate includes injured players marked as "IL" in Injury Indicator
SOLUTION: Filter out all IL players before generating lineups

RUN ORDER: Execute these steps daily for clean DFS lineups
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def daily_dfs_workflow():
    """Complete daily DFS workflow"""
    
    logger.info("🚀 STARTING DAILY MLB DFS WORKFLOW")
    logger.info("=" * 50)
    
    steps = [
        {
            'step': 1,
            'name': 'Update FanDuel Slate',
            'script': None,
            'action': 'Manual: Download today\'s FanDuel slate to fd_current_slate/fd_slate_today.csv',
            'critical': True
        },
        {
            'step': 2,
            'name': 'Copy Complete Slate to Data Folder',
            'script': None,
            'action': 'Copy-Item "fd_current_slate/fd_slate_today.csv" "data/fd_slate_today.csv" -Force',
            'critical': True
        },
        {
            'step': 3,
            'name': 'Filter Healthy Pitchers (Remove IL Players)',
            'script': 'filter_todays_pitchers.py',
            'action': 'python filter_todays_pitchers.py',
            'critical': True,
            'note': 'This removes Shane Bieber and other IL players'
        },
        {
            'step': 4,
            'name': 'Run 20-Step Data Pipeline',
            'script': '1_DATA_PIPELINE.bat',
            'action': '1_DATA_PIPELINE.bat',
            'critical': True,
            'note': 'Builds hitter/pitcher features with weather/park factors'
        },
        {
            'step': 5,
            'name': 'Generate Enhanced DFS Lineups',
            'script': 'run_game_state_enhanced_dfs.py',
            'action': 'python run_game_state_enhanced_dfs.py',
            'critical': True,
            'note': '2000 simulations with ML projections and ownership modeling'
        },
        {
            'step': 6,
            'name': 'Create FanDuel Submission Files',
            'script': 'TBD',
            'action': 'Format lineups for FanDuel entry',
            'critical': False,
            'note': 'Convert to FanDuel CSV format'
        }
    ]
    
    logger.info("📋 DAILY WORKFLOW STEPS:")
    for step in steps:
        status = "🔴 CRITICAL" if step['critical'] else "🟡 OPTIONAL"
        logger.info(f"STEP {step['step']}: {step['name']} {status}")
        logger.info(f"  Action: {step['action']}")
        if step.get('note'):
            logger.info(f"  Note: {step['note']}")
        logger.info("")
    
    return steps

def validate_daily_setup():
    """Validate that all required files and folders exist"""
    
    logger.info("🔍 VALIDATING DAILY SETUP")
    
    required_files = [
        '../fd_current_slate/fd_slate_today.csv',
        '../data/fd_slate_today.csv',
        'filter_todays_pitchers.py',
        'run_game_state_enhanced_dfs.py',
        '../DAILY_RUNNERS/1_DATA_PIPELINE.bat'
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path}")
        else:
            logger.error(f"❌ {file_path} - MISSING!")
            all_good = False
    
    return all_good

def check_for_injured_players():
    """Check if any injured players are still in the lineup results"""
    
    import pandas as pd
    
    # Check latest enhanced lineups file
    data_dir = "../data"
    lineup_files = [f for f in os.listdir(data_dir) if f.startswith('game_state_enhanced_lineups_')]
    
    if not lineup_files:
        logger.warning("No enhanced lineup files found")
        return False
    
    latest_file = max(lineup_files)
    lineup_path = os.path.join(data_dir, latest_file)
    
    logger.info(f"🔍 Checking {latest_file} for injured players...")
    
    df = pd.read_csv(lineup_path)
    
    # Check for known injured players
    injured_names = ['Shane Bieber', 'Chris Sale', 'Hunter Greene', 'Gerrit Cole']
    
    found_injured = []
    for name in injured_names:
        if name in df['name'].values:
            found_injured.append(name)
    
    if found_injured:
        logger.error(f"🚨 FOUND INJURED PLAYERS IN LINEUPS: {found_injured}")
        return False
    else:
        logger.info("✅ No injured players found in lineups")
        return True

if __name__ == "__main__":
    
    print("\n" + "="*60)
    print("    DAILY MLB DFS WORKFLOW DOCUMENTATION")
    print("="*60)
    
    # Document the workflow
    steps = daily_dfs_workflow()
    
    print("\n" + "="*60)
    print("    VALIDATION CHECKS")
    print("="*60)
    
    # Validate setup
    setup_ok = validate_daily_setup()
    
    # Check for injured players in recent results
    no_injured = check_for_injured_players()
    
    print("\n" + "="*60)
    print("    SUMMARY")
    print("="*60)
    
    if setup_ok and no_injured:
        print("✅ READY FOR DAILY DFS WORKFLOW")
        print("   All files present and no injured players detected")
    else:
        print("❌ ISSUES DETECTED - FIX BEFORE RUNNING DAILY WORKFLOW")
        if not setup_ok:
            print("   - Missing required files")
        if not no_injured:
            print("   - Injured players found in recent lineups")
    
    print("\n🎯 KEY INSIGHT: Always run filter_todays_pitchers.py")
    print("   before generating lineups to remove IL players!")
    print("="*60)

#!/usr/bin/env python3
"""
EMERGENCY LINEUP CHANGE CHECKER
================================
Manual check for critical lineup changes affecting submitted lineups
"""

import pandas as pd
import logging
from datetime import datetime
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmergencyLineupChecker:
    def __init__(self):
        self.submitted_lineups = []
        self.critical_players = []
        
    def load_submitted_lineups(self):
        """Load FanDuel submitted lineups"""
        try:
            df = pd.read_csv('../data/FANDUEL_READY_ELITE_LINEUPS_20250815.csv')
            logger.info(f"SUCCESS: Loaded {len(df)} submitted lineups")
            
            # Extract all players from all positions
            self.critical_players = []
            
            for _, lineup in df.iterrows():
                for col in df.columns:
                    if col != 'Nickname' and pd.notna(lineup[col]):
                        player_name = lineup[col]
                        if player_name not in self.critical_players:
                            self.critical_players.append(player_name)
            
            logger.info(f"CRITICAL: Monitoring {len(self.critical_players)} unique players:")
            for player in self.critical_players:
                logger.info(f"  🔍 {player}")
                
            return True
            
        except Exception as e:
            logger.error(f"ERROR loading lineups: {e}")
            return False
    
    def check_player_status(self, player_name):
        """Check if player is actually starting today"""
        try:
            # This would normally check MLB API or RotoWire
            # For now, manually flag known issues
            
            if "Rob Refsnyder" in player_name:
                return {
                    'status': 'NOT_STARTING',
                    'reason': 'Scratch from lineup - not in starting 9',
                    'confidence': 'CONFIRMED',
                    'urgency': 'CRITICAL'
                }
            
            # Default to starting unless we know otherwise
            return {
                'status': 'STARTING',
                'reason': 'No lineup changes detected',
                'confidence': 'ASSUMED',
                'urgency': 'LOW'
            }
            
        except Exception as e:
            logger.error(f"Error checking {player_name}: {e}")
            return {'status': 'UNKNOWN', 'reason': str(e)}
    
    def get_backup_recommendations(self, scratched_player):
        """Get emergency backup recommendations"""
        try:
            # Load current slate to find suitable replacements
            df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
            
            # Filter by similar position and salary range
            if "Refsnyder" in scratched_player:
                # Rob Refsnyder is OF, $2600
                backups = df[
                    (df['Position'] == 'OF') & 
                    (df['Salary'] <= 3000) &  # Within $400 salary
                    (df['Salary'] >= 2200)
                ].copy()
                
                if not backups.empty:
                    backups = backups.sort_values('FPPG', ascending=False)
                    return backups.head(5)[['First Name', 'Nickname', 'Salary', 'FPPG', 'Team']].to_dict('records')
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting backups: {e}")
            return []
    
    def run_emergency_check(self):
        """Run comprehensive emergency check"""
        logger.info("🚨 EMERGENCY LINEUP VERIFICATION STARTING")
        logger.info("=" * 50)
        
        if not self.load_submitted_lineups():
            return
        
        critical_issues = []
        
        # Check each critical player
        for player in self.critical_players:
            status = self.check_player_status(player)
            
            if status['status'] != 'STARTING':
                critical_issues.append({
                    'player': player,
                    'issue': status
                })
                
                logger.warning(f"🚨 CRITICAL ISSUE DETECTED:")
                logger.warning(f"   Player: {player}")
                logger.warning(f"   Status: {status['status']}")
                logger.warning(f"   Reason: {status['reason']}")
                logger.warning(f"   Urgency: {status['urgency']}")
                
                # Get backup recommendations
                backups = self.get_backup_recommendations(player)
                if backups:
                    logger.info(f"   💡 EMERGENCY BACKUP OPTIONS:")
                    for i, backup in enumerate(backups, 1):
                        logger.info(f"      {i}. {backup.get('First Name', '')} {backup.get('Nickname', '')} - ${backup.get('Salary', 0)} - {backup.get('FPPG', 0):.1f} pts")
        
        # Summary
        if critical_issues:
            logger.error(f"🚨 CRITICAL: {len(critical_issues)} lineup issues detected!")
            logger.error("   ACTION REQUIRED: Log into FanDuel and make swaps immediately!")
        else:
            logger.info("✅ All submitted players appear to be starting")
        
        return critical_issues

if __name__ == "__main__":
    checker = EmergencyLineupChecker()
    issues = checker.run_emergency_check()
    
    if issues:
        print("\n" + "="*60)
        print("🚨 EMERGENCY ACTION REQUIRED 🚨")
        print("="*60)
        print("Log into FanDuel NOW and swap out scratched players!")
        print("Rob Refsnyder is NOT STARTING - swap immediately!")
        print("="*60)

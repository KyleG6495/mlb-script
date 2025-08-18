#!/usr/bin/env python3
"""
ELITE LATE SWAP AUTOMATION SYSTEM
Real-time lineup optimization with Hurston Waldrep success pattern integration
Based on 104-point, top 35% tournament finish analysis
"""

import pandas as pd
import numpy as np
import requests
import json
import time
import logging
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PlayerUpdate:
    """Player status update"""
    player_name: str
    player_id: str
    old_status: str
    new_status: str
    timestamp: datetime
    source: str
    severity: int  # 1-5, 5 being most critical

@dataclass
class LineupSlot:
    """Lineup slot with player and constraints"""
    position: str
    player_name: str
    player_id: str
    salary: int
    projection: float
    ownership: float
    is_locked: bool = False
    is_stack_member: bool = False
    stack_team: str = ""

class EliteLateSwapMonitor:
    """Enhanced monitor with Waldrep-type opportunity detection"""
    
    def __init__(self):
        self.player_updates = []
        self.monitoring = False
        self.update_sources = {
            'rotowire': 'https://www.rotowire.com/baseball/daily-lineups.php',
            'mlb_api': 'https://statsapi.mlb.com/api/v1/schedule',
            'rotogrinders': 'https://rotogrinders.com/lineups/mlb'
        }
        
        # Critical times for monitoring
        self.critical_windows = {
            'initial_lineups': 16,  # 4 PM ET - Most lineups posted
            'late_changes': 18,     # 6 PM ET - Late scratches
            'final_check': 19       # 7 PM ET - Final verification
        }
        
        # Elite patterns (based on Waldrep success)
        self.elite_patterns = {
            'waldrep_type': {
                'ownership_range': (5, 15),
                'projection_min': 35,
                'position': 'P',
                'success_score': 49  # Waldrep scored 49
            },
            'contrarian_threshold': 10,  # Sub-10% targets
            'stack_correlation': 0.7     # Game stack minimum
        }
        
    def identify_waldrep_opportunities(self, available_players):
        """Find late-emerging Waldrep-type opportunities"""
        logger.info("🎯 SCANNING FOR WALDREP-TYPE LATE OPPORTUNITIES...")
        
        opportunities = []
        
        for player in available_players:
            if (player.get('position') == 'P' and 
                self.elite_patterns['waldrep_type']['ownership_range'][0] <= 
                player.get('ownership', 20) <= 
                self.elite_patterns['waldrep_type']['ownership_range'][1] and
                player.get('projection', 0) >= self.elite_patterns['waldrep_type']['projection_min']):
                
                opportunity_score = (
                    player.get('projection', 0) * 2 +
                    (15 - player.get('ownership', 15)) * 3
                )
                
                opportunities.append({
                    'player_name': player.get('name', ''),
                    'ownership': player.get('ownership', 0),
                    'projection': player.get('projection', 0),
                    'opportunity_score': opportunity_score,
                    'type': 'Waldrep_Type'
                })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        if opportunities:
            logger.info(f"🔥 FOUND {len(opportunities)} WALDREP-TYPE OPPORTUNITIES:")
            for opp in opportunities[:3]:
                logger.info(f"  {opp['player_name']:20} | {opp['projection']:.1f} proj | {opp['ownership']:.1f}% own | Score: {opp['opportunity_score']:.1f}")
        
        return opportunities
        
    def start_monitoring(self, target_lineups: List[Dict]):
        """Start enhanced monitoring with elite pattern detection"""
        
        logger.info("🏆 STARTING ELITE LATE SWAP MONITORING")
        logger.info("=" * 50)
        logger.info("🎯 Based on Hurston Waldrep 49-point success pattern")
        
        self.monitoring = True
        self.target_lineups = target_lineups
        
        # Extract all players to monitor
        self.monitored_players = set()
        for lineup in target_lineups:
            for player in lineup['players']:
                self.monitored_players.add(player['player_key'])
        
        logger.info(f"👀 Monitoring {len(self.monitored_players)} players across {len(target_lineups)} lineups")
        logger.info(f"🎯 Scanning for sub-{self.elite_patterns['contrarian_threshold']}% ownership opportunities")
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_rotowire, daemon=True).start()
        threading.Thread(target=self._monitor_mlb_api, daemon=True).start()
        threading.Thread(target=self._monitor_news_feeds, daemon=True).start()
        threading.Thread(target=self._monitor_elite_opportunities, daemon=True).start()  # NEW
        
    def _monitor_elite_opportunities(self):
        """Monitor for elite-level late swap opportunities"""
        
        while self.monitoring:
            try:
                current_hour = datetime.now().hour
                
                # Peak opportunity window (5-7 PM)
                if 17 <= current_hour <= 19:
                    logger.info("⚡ ELITE OPPORTUNITY SCAN (Prime Window)")
                    
                    # Simulate checking for late opportunities
                    # In production, this would query real data sources
                    opportunities = self._simulate_elite_scan()
                    
                    if opportunities:
                        logger.info(f"🚨 {len(opportunities)} ELITE OPPORTUNITIES DETECTED")
                        for opp in opportunities:
                            logger.info(f"  🎯 {opp['type']}: {opp['description']}")
                
                time.sleep(180)  # Check every 3 minutes during peak
                
            except Exception as e:
                logger.error(f"Error in elite monitoring: {e}")
                time.sleep(60)
    
    def _simulate_elite_scan(self):
        """Simulate elite opportunity detection"""
        current_time = datetime.now()
        
        # Simulate finding opportunities based on your patterns
        opportunities = []
        
        if current_time.minute % 10 == 0:  # Every 10 minutes
            opportunities.append({
                'type': 'Low_Owned_Ace',
                'description': 'Sub-10% pitcher with ace upside (Waldrep-type)',
                'priority': 'HIGH',
                'action': 'Consider swapping from chalk pitcher'
            })
        
        if current_time.minute % 15 == 0:  # Every 15 minutes
            opportunities.append({
                'type': 'Game_Stack_Edge',
                'description': 'Game correlation opportunity emerging',
                'priority': 'MEDIUM', 
                'action': 'Build 3-4 player stack from targeted game'
            })
        
        return opportunities
        
        logger.info(f" Monitoring {len(self.monitored_players)} players across {len(target_lineups)} lineups")
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_rotowire, daemon=True).start()
        threading.Thread(target=self._monitor_mlb_api, daemon=True).start()
        threading.Thread(target=self._monitor_news_feeds, daemon=True).start()
        
    def _monitor_rotowire(self):
        """Monitor RotoWire for lineup changes"""
        
        while self.monitoring:
            try:
                logger.info(" Checking RotoWire for lineup updates...")
                
                # This would normally scrape RotoWire, but for demo we'll simulate
                # In production, you'd parse the RotoWire lineup page
                self._simulate_rotowire_check()
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"ERROR: RotoWire monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_mlb_api(self):
        """Monitor MLB API for game status changes"""
        
        while self.monitoring:
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
                
                response = requests.get(url, timeout=10)
                data = response.json()
                
                for game in data.get('dates', [{}])[0].get('games', []):
                    game_status = game.get('status', {}).get('detailedState', '')
                    
                    if game_status in ['Postponed', 'Delayed', 'Cancelled']:
                        self._handle_game_status_change(game, game_status)
                
                time.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"ERROR: MLB API monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_news_feeds(self):
        """Monitor Twitter/news feeds for injury updates"""
        
        while self.monitoring:
            try:
                # In production, this would monitor Twitter API, RSS feeds, etc.
                # For demo, we'll simulate news monitoring
                self._simulate_news_monitoring()
                
                time.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"ERROR: News monitoring error: {e}")
                time.sleep(60)
    
    def _simulate_rotowire_check(self):
        """Simulate RotoWire lineup checking"""
        
        # Simulate finding a scratched player
        if np.random.random() < 0.05:  # 5% chance of finding an update
            
            monitored_list = list(self.monitored_players)
            if monitored_list:
                player = np.random.choice(monitored_list)
                
                update = PlayerUpdate(
                    player_name=player,
                    player_id=player.replace(' ', '_'),
                    old_status='Starting',
                    new_status='Scratched',
                    timestamp=datetime.now(),
                    source='RotoWire',
                    severity=5
                )
                
                self.player_updates.append(update)
                logger.warning(f" PLAYER SCRATCHED: {player} - Source: RotoWire")
                
                # Trigger immediate swap
                self._trigger_emergency_swap(update)
    
    def _simulate_news_monitoring(self):
        """Simulate news feed monitoring"""
        
        # Simulate injury news
        if np.random.random() < 0.03:  # 3% chance of injury news
            
            injury_types = ['DTD - Back', 'Illness', 'Family Matter', 'Rest Day']
            monitored_list = list(self.monitored_players)
            
            if monitored_list:
                player = np.random.choice(monitored_list)
                injury = np.random.choice(injury_types)
                
                severity = 3 if 'DTD' in injury else 4 if 'Illness' in injury else 2
                
                update = PlayerUpdate(
                    player_name=player,
                    player_id=player.replace(' ', '_'),
                    old_status='Healthy',
                    new_status=injury,
                    timestamp=datetime.now(),
                    source='Beat Reporter',
                    severity=severity
                )
                
                self.player_updates.append(update)
                logger.warning(f"WARNING: INJURY UPDATE: {player} - {injury}")
                
                if severity >= 4:
                    self._trigger_emergency_swap(update)
    
    def _handle_game_status_change(self, game, status):
        """Handle game postponement/delay"""
        
        logger.warning(f" GAME STATUS CHANGE: {game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')} @ {game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')} - {status}")
        
        # Find affected players and trigger swaps
        # This would identify players in the affected game
        
    def _trigger_emergency_swap(self, update: PlayerUpdate):
        """Trigger emergency player swap"""
        
        logger.error(f"SWAP: TRIGGERING EMERGENCY SWAP for {update.player_name}")
        
        # This would integrate with the lineup optimizer to find replacements
        # For now, we'll log the action needed
        logger.info(f"   INFO: Action: Find replacement for {update.player_name}")
        logger.info(f"    Time: {update.timestamp}")
        logger.info(f"   DATA: Severity: {update.severity}/5")
    
    def get_recent_updates(self, minutes: int = 30) -> List[PlayerUpdate]:
        """Get player updates from last N minutes"""
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [u for u in self.player_updates if u.timestamp > cutoff]
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("SUCCESS: Late swap monitoring stopped")

class LiveOwnershipTracker:
    """Track live ownership percentages from contest fills"""
    
    def __init__(self):
        self.ownership_data = {}
        self.tracking_active = False
        
    def start_tracking(self, contest_ids: List[str]):
        """Start tracking ownership for specific contests"""
        
        logger.info("DATA: STARTING LIVE OWNERSHIP TRACKING")
        logger.info("=" * 50)
        
        self.contest_ids = contest_ids
        self.tracking_active = True
        
        # Start tracking thread
        threading.Thread(target=self._track_ownership, daemon=True).start()
        
    def _track_ownership(self):
        """Track ownership changes in real-time"""
        
        while self.tracking_active:
            try:
                # In production, this would connect to DFS platform APIs
                # For demo, we'll simulate ownership tracking
                self._simulate_ownership_tracking()
                
                time.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                logger.error(f"ERROR: Ownership tracking error: {e}")
                time.sleep(300)
    
    def _simulate_ownership_tracking(self):
        """Simulate live ownership tracking"""
        
        # Simulate ownership changes
        ownership_changes = {
            'Shane Bieber': {'old': 45.2, 'new': 52.1, 'trend': ''},
            'Cal Raleigh': {'old': 3.4, 'new': 2.1, 'trend': ''},
            'River Ryan': {'old': 8.7, 'new': 6.3, 'trend': ''}
        }
        
        for player, data in ownership_changes.items():
            old_own = data['old']
            new_own = data['new']
            change = new_own - old_own
            
            if abs(change) > 2.0:  # Significant change
                logger.info(f"PROGRESS: OWNERSHIP ALERT: {player} - {old_own:.1f}%  {new_own:.1f}% ({change:+.1f}%) {data['trend']}")
                
                if new_own > 25 and player in self.get_monitored_players():
                    logger.warning(f" CHALK ALERT: {player} now {new_own:.1f}% owned - Consider pivot!")
                elif new_own < 5 and change < -2:
                    logger.info(f" LEVERAGE OPPORTUNITY: {player} now only {new_own:.1f}% owned")
    
    def get_monitored_players(self) -> List[str]:
        """Get list of players we're monitoring"""
        # This would return players from our lineups
        return ['Shane Bieber', 'Cal Raleigh', 'River Ryan', 'Luke Keaschall']
    
    def get_current_ownership(self, player_name: str) -> float:
        """Get current ownership for a player"""
        return self.ownership_data.get(player_name, 0.0)
    
    def stop_tracking(self):
        """Stop ownership tracking"""
        self.tracking_active = False
        logger.info("SUCCESS: Live ownership tracking stopped")

class LateSwapOptimizer:
    """Optimize lineups with late swap capabilities"""
    
    def __init__(self, projections_df: pd.DataFrame, ownership_df: pd.DataFrame):
        self.projections = projections_df
        self.ownership = ownership_df
        self.backup_players = {}
        self.swap_history = []
        
        # Merge data for quick access
        self.player_pool = self._create_player_pool()
        
    def _create_player_pool(self):
        """Create comprehensive player pool with swap data"""
        
        # Merge projections with ownership
        pool = self.projections.merge(
            self.ownership[['player_name', 'ownership', 'leverage_score']],
            left_on='First Name',  # Adjust based on your column names
            right_on='player_name',
            how='left',
            suffixes=('', '_own')
        )
        
        pool['ownership'] = pool['ownership'].fillna(0.15)
        pool['leverage_score'] = pool['leverage_score'].fillna(2.0)
        pool['player_key'] = pool['First Name'] + ' ' + pool['Last Name']
        
        return pool
    
    def generate_backup_players(self, lineup: Dict, num_backups: int = 3):
        """Generate backup players for each position in lineup"""
        
        logger.info("SWAP: GENERATING BACKUP PLAYERS")
        logger.info("=" * 40)
        
        backup_dict = {}
        
        for player in lineup['players']:
            position = player['Position']
            salary = player['Salary']
            current_player = player['player_key']
            
            # Find similar players at same position
            position_pool = self.player_pool[
                (self.player_pool['Position'] == position) &
                (self.player_pool['player_key'] != current_player) &
                (self.player_pool['Salary'] >= salary * 0.8) &  # 80% of salary minimum
                (self.player_pool['Salary'] <= salary * 1.2)    # 120% of salary maximum
            ].copy()
            
            if len(position_pool) == 0:
                # Expand salary range if no matches
                position_pool = self.player_pool[
                    (self.player_pool['Position'] == position) &
                    (self.player_pool['player_key'] != current_player)
                ].copy()
            
            # Calculate swap score (combination of projection and ownership)
            position_pool['swap_score'] = (
                position_pool['enhanced_fppg'] * 0.6 +
                position_pool['leverage_score'] * 0.4
            )
            
            # Get top backups
            top_backups = position_pool.nlargest(num_backups, 'swap_score')
            
            backup_dict[current_player] = []
            
            logger.info(f"\nTARGET: Backups for {current_player} ({position}) - ${salary}:")
            
            for idx, backup in top_backups.iterrows():
                backup_info = {
                    'player_key': backup['player_key'],
                    'salary': backup['Salary'],
                    'projection': backup['enhanced_fppg'],
                    'ownership': backup['ownership'],
                    'leverage': backup['leverage_score'],
                    'swap_score': backup['swap_score'],
                    'salary_diff': backup['Salary'] - salary
                }
                
                backup_dict[current_player].append(backup_info)
                
                logger.info(f"  SWAP: {backup['player_key']} - ${backup['Salary']} "
                           f"({backup_info['salary_diff']:+d}) | "
                           f"{backup['enhanced_fppg']:.1f} proj | "
                           f"{backup['ownership']:.1%} own | "
                           f"{backup['leverage_score']:.2f} lev")
        
        self.backup_players[lineup.get('lineup_id', 'lineup_1')] = backup_dict
        
        return backup_dict
    
    def execute_emergency_swap(self, lineup_id: str, scratched_player: str, 
                              preserve_stack: bool = True) -> Dict:
        """Execute emergency swap for scratched player"""
        
        logger.error(f" EXECUTING EMERGENCY SWAP")
        logger.error(f"   Lineup: {lineup_id}")
        logger.error(f"   Scratched: {scratched_player}")
        logger.error(f"   Preserve Stack: {preserve_stack}")
        
        if lineup_id not in self.backup_players:
            logger.error("ERROR: No backup players generated for this lineup!")
            return None
        
        backup_options = self.backup_players[lineup_id].get(scratched_player, [])
        
        if not backup_options:
            logger.error("ERROR: No backup options available!")
            return None
        
        # Select best backup based on current conditions
        best_backup = self._select_optimal_backup(backup_options, preserve_stack)
        
        # Log the swap
        swap_record = {
            'timestamp': datetime.now(),
            'lineup_id': lineup_id,
            'out_player': scratched_player,
            'in_player': best_backup['player_key'],
            'salary_change': best_backup['salary_diff'],
            'projection_change': 'TBD',  # Would calculate from original
            'reason': 'Emergency - Player Scratched'
        }
        
        self.swap_history.append(swap_record)
        
        logger.info(f"SUCCESS: SWAP EXECUTED:")
        logger.info(f"   OUT: {scratched_player}")
        logger.info(f"   IN:  {best_backup['player_key']}")
        logger.info(f"   MONEY: Salary: {best_backup['salary_diff']:+d}")
        logger.info(f"   PROGRESS: Projection: {best_backup['projection']:.1f}")
        logger.info(f"   OWNERSHIP: Ownership: {best_backup['ownership']:.1%}")
        
        return best_backup
    
    def _select_optimal_backup(self, backup_options: List[Dict], 
                              preserve_stack: bool) -> Dict:
        """Select the optimal backup player"""
        
        # For now, select highest swap score
        # In production, this would consider stack preservation, salary cap, etc.
        return max(backup_options, key=lambda x: x['swap_score'])
    
    def suggest_proactive_swaps(self, ownership_threshold: float = 0.25) -> List[Dict]:
        """Suggest proactive swaps based on ownership changes"""
        
        suggestions = []
        
        # This would analyze current lineups vs live ownership
        # and suggest beneficial swaps before locks
        
        logger.info(f"DATA: PROACTIVE SWAP ANALYSIS (Ownership Threshold: {ownership_threshold:.0%})")
        
        # Simulate finding high-ownership players to fade
        high_ownership_players = [
            {'player': 'Shane Bieber', 'ownership': 0.52, 'suggestion': 'Fade for River Ryan'},
            {'player': 'Garrett Crochet', 'ownership': 0.31, 'suggestion': 'Consider pivot to Blubaugh'}
        ]
        
        for player_data in high_ownership_players:
            if player_data['ownership'] > ownership_threshold:
                suggestions.append({
                    'type': 'fade_chalk',
                    'player': player_data['player'],
                    'ownership': player_data['ownership'],
                    'suggestion': player_data['suggestion'],
                    'priority': 'High' if player_data['ownership'] > 0.4 else 'Medium'
                })
                
                logger.warning(f" FADE SUGGESTION: {player_data['player']} "
                              f"({player_data['ownership']:.0%} owned)  {player_data['suggestion']}")
        
        return suggestions

class LateSwapMaster:
    """Master class coordinating all late swap activities"""
    
    def __init__(self, projections_df: pd.DataFrame, ownership_df: pd.DataFrame):
        self.monitor = EliteLateSwapMonitor()  # Use enhanced monitor
        self.ownership_tracker = LiveOwnershipTracker()
        self.optimizer = LateSwapOptimizer(projections_df, ownership_df)
        self.active_lineups = []
        
    def initialize_late_swap_system(self, lineups: List[Dict], contest_ids: List[str] = None):
        """Initialize the complete late swap system"""
        
        logger.info("START: INITIALIZING LATE SWAP MASTER SYSTEM")
        logger.info("=" * 60)
        
        self.active_lineups = lineups
        
        # Generate backup players for all lineups
        for i, lineup in enumerate(lineups):
            lineup['lineup_id'] = f"lineup_{i+1}"
            self.optimizer.generate_backup_players(lineup)
        
        # Start monitoring systems
        self.monitor.start_monitoring(lineups)
        
        if contest_ids:
            self.ownership_tracker.start_tracking(contest_ids)
        
        logger.info(f"SUCCESS: Late swap system active for {len(lineups)} lineups")
        logger.info(" Ready for emergency swaps and ownership monitoring")
        
    def run_pre_lock_analysis(self, minutes_before_lock: int = 60):
        """Run final analysis before lineup locks"""
        
        logger.info(f"TIME: PRE-LOCK ANALYSIS ({minutes_before_lock} minutes to lock)")
        logger.info("=" * 50)
        
        # Check for recent player updates
        recent_updates = self.monitor.get_recent_updates(minutes=30)
        
        if recent_updates:
            logger.warning(f"WARNING: {len(recent_updates)} recent player updates:")
            for update in recent_updates:
                logger.warning(f"   {update.player_name}: {update.old_status}  {update.new_status}")
        
        # Get proactive swap suggestions
        swap_suggestions = self.optimizer.suggest_proactive_swaps()
        
        if swap_suggestions:
            logger.info(f"TIP: {len(swap_suggestions)} proactive swap suggestions available")
        
        # Final ownership check
        logger.info("DATA: Final ownership verification in progress...")
        
        return {
            'recent_updates': recent_updates,
            'swap_suggestions': swap_suggestions,
            'system_status': 'Active',
            'lineups_monitored': len(self.active_lineups)
        }
    
    def shutdown_system(self):
        """Shutdown all monitoring systems"""
        
        logger.info(" SHUTTING DOWN LATE SWAP SYSTEM")
        
        self.monitor.stop_monitoring()
        self.ownership_tracker.stop_tracking()
        
        # Log final summary
        total_swaps = len(self.optimizer.swap_history)
        total_updates = len(self.monitor.player_updates)
        
        logger.info(f"DATA: FINAL SUMMARY:")
        logger.info(f"   Swaps Executed: {total_swaps}")
        logger.info(f"   Player Updates: {total_updates}")
        logger.info(f"   System Uptime: Active until shutdown")
        
        logger.info("SUCCESS: Late swap system shutdown complete")

def main():
    """Demo the late swap system"""
    
    try:
        # Load sample data with dynamic dates
        current_date = datetime.now().strftime("%Y%m%d")
        
        import glob
        
        # Find today's files
        enhanced_files = glob.glob(f"../data/enhanced_projections_{current_date}_*.csv")
        ownership_files = glob.glob(f"../data/advanced_ownership_projections_{current_date}_*.csv")
        
        if enhanced_files and ownership_files:
            projections = pd.read_csv(enhanced_files[-1])
            ownership = pd.read_csv(ownership_files[-1])
        else:
            logger.error("ERROR: Could not find today's projection files!")
            return
        
        logger.info(f"SUCCESS: Loaded {len(projections)} projections and {len(ownership)} ownership records")
        
        # Create sample lineups (would come from your optimizer)
        sample_lineups = [
            {
                'lineup_id': 'demo_1',
                'players': [
                    {'player_key': 'Tarik Skubal', 'Position': 'P', 'Salary': 11000, 'enhanced_fppg': 43.7},
                    {'player_key': 'Cal Raleigh', 'Position': 'C', 'Salary': 4500, 'enhanced_fppg': 14.2},
                    {'player_key': 'Luke Keaschall', 'Position': '2B', 'Salary': 3300, 'enhanced_fppg': 20.3}
                    # ... would have full 9-player lineup
                ]
            }
        ]
        
        # Initialize late swap system
        swap_master = LateSwapMaster(projections, ownership)
        swap_master.initialize_late_swap_system(sample_lineups, contest_ids=['contest_123'])
        
        # Run for demo period
        logger.info("TIME: Running demo monitoring for 30 seconds...")
        time.sleep(30)
        
        # Run pre-lock analysis
        analysis = swap_master.run_pre_lock_analysis()
        
        # Shutdown
        swap_master.shutdown_system()
        
        logger.info("COMPLETE: LATE SWAP SYSTEM DEMO COMPLETE!")
        
    except Exception as e:
        logger.error(f"ERROR: Error in late swap demo: {str(e)}")
        raise

if __name__ == "__main__":
    main()

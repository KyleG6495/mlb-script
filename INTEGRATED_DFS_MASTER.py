#!/usr/bin/env python3
"""
INTEGRATED LATE SWAP & OWNERSHIP SYSTEM
Complete real-time DFS optimization with late swaps and ownership monitoring
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from LATE_SWAP_AUTOMATION import LateSwapMaster, PlayerUpdate
from LIVE_OWNERSHIP_TRACKER import RealTimeOwnershipTracker, OwnershipAlert

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedDFSOptimizer:
    """Master system integrating late swap and ownership monitoring"""
    
    def __init__(self, projections_df: pd.DataFrame, ownership_df: pd.DataFrame):
        self.projections = projections_df
        self.ownership = ownership_df
        
        # Initialize subsystems
        self.late_swap_master = LateSwapMaster(projections_df, ownership_df)
        self.ownership_tracker = None
        
        # System state
        self.active_lineups = []
        self.target_players = []
        self.contest_ids = []
        self.system_active = False
        
        # Decision thresholds
        self.decision_thresholds = {
            'emergency_swap_trigger': 5,      # Severity 5 = immediate swap
            'ownership_fade_threshold': 0.30,  # Fade players above 30%
            'leverage_opportunity': 0.05,      # Target players below 5%
            'minutes_before_lock': 120,        # Start intensive monitoring 2 hours before
            'final_check_minutes': 30          # Final check 30 minutes before lock
        }
        
        # Integration events
        self.integration_events = []
        
    def initialize_complete_system(self, lineups: List[Dict], contest_ids: List[str],
                                 game_times: List[datetime] = None):
        """Initialize the complete integrated system"""
        
        logger.info("START: INITIALIZING INTEGRATED DFS OPTIMIZATION SYSTEM")
        logger.info("=" * 70)
        
        self.active_lineups = lineups
        self.contest_ids = contest_ids
        
        # Extract target players from lineups
        self.target_players = []
        for lineup in lineups:
            for player in lineup['players']:
                if player['player_key'] not in self.target_players:
                    self.target_players.append(player['player_key'])
        
        logger.info(f"INFO: Managing {len(lineups)} lineups")
        logger.info(f"TARGET: Monitoring {len(self.target_players)} unique players")
        logger.info(f"LINEUP: Tracking {len(contest_ids)} contests")
        
        # Initialize late swap system
        self.late_swap_master.initialize_late_swap_system(lineups, contest_ids)
        
        # Initialize ownership tracking
        self.ownership_tracker = RealTimeOwnershipTracker(self.target_players)
        self.ownership_tracker.start_tracking(contest_ids, check_interval=300)  # 5 minutes
        
        # Start integration monitoring
        self.system_active = True
        threading.Thread(target=self._integration_monitor, daemon=True).start()
        
        logger.info("SUCCESS: INTEGRATED SYSTEM FULLY ACTIVE")
        logger.info(" Ready for late swaps and ownership optimization")
        
    def _integration_monitor(self):
        """Monitor both systems and make integrated decisions"""
        
        while self.system_active:
            try:
                # Check for player updates from late swap system
                recent_updates = self.late_swap_master.monitor.get_recent_updates(minutes=10)
                
                # Check for ownership alerts
                ownership_alerts = []
                if self.ownership_tracker:
                    ownership_alerts = self.ownership_tracker.alert_system.get_active_alerts(minutes=10)
                
                # Make integrated decisions
                if recent_updates or ownership_alerts:
                    self._process_integrated_alerts(recent_updates, ownership_alerts)
                
                # Periodic system health check
                self._system_health_check()
                
                time.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"ERROR: Integration monitor error: {e}")
                time.sleep(60)
    
    def _process_integrated_alerts(self, player_updates: List[PlayerUpdate], 
                                 ownership_alerts: List[OwnershipAlert]):
        """Process alerts from both systems and make coordinated decisions"""
        
        logger.info(" PROCESSING INTEGRATED ALERTS")
        logger.info("=" * 40)
        
        # Process player updates (injuries, scratches)
        for update in player_updates:
            if update.severity >= self.decision_thresholds['emergency_swap_trigger']:
                
                logger.error(f" EMERGENCY SWAP TRIGGERED: {update.player_name}")
                
                # Execute emergency swap
                for lineup in self.active_lineups:
                    lineup_id = lineup.get('lineup_id', 'unknown')
                    
                    # Check if player is in this lineup
                    lineup_players = [p['player_key'] for p in lineup['players']]
                    if update.player_name in lineup_players:
                        
                        # Execute swap
                        swap_result = self.late_swap_master.optimizer.execute_emergency_swap(
                            lineup_id, update.player_name, preserve_stack=True
                        )
                        
                        if swap_result:
                            # Log integration event
                            self._log_integration_event(
                                event_type='emergency_swap',
                                trigger='player_scratch',
                                details=f"Swapped {update.player_name} for {swap_result['player_key']}"
                            )
        
        # Process ownership alerts (chalk rising, leverage opportunities)
        for alert in ownership_alerts:
            
            if alert.alert_type == 'chalk_rising' and alert.new_ownership > self.decision_thresholds['ownership_fade_threshold']:
                
                logger.warning(f"PROGRESS: CHALK FADE OPPORTUNITY: {alert.player_name} now {alert.new_ownership:.1%}")
                
                # Check if we have this player in any lineups
                affected_lineups = self._find_lineups_with_player(alert.player_name)
                
                if affected_lineups:
                    logger.warning(f"   Found in {len(affected_lineups)} lineups - recommend fade")
                    
                    # Log for manual review (in production, could auto-fade based on rules)
                    self._log_integration_event(
                        event_type='fade_recommendation',
                        trigger='ownership_spike',
                        details=f"{alert.player_name} ownership spiked to {alert.new_ownership:.1%}"
                    )
            
            elif alert.alert_type == 'leverage_falling' and alert.new_ownership < self.decision_thresholds['leverage_opportunity']:
                
                logger.info(f" LEVERAGE OPPORTUNITY: {alert.player_name} dropped to {alert.new_ownership:.1%}")
                
                # Check if we can add this player to any lineups
                self._evaluate_leverage_addition(alert.player_name, alert.new_ownership)
    
    def _find_lineups_with_player(self, player_name: str) -> List[str]:
        """Find which lineups contain a specific player"""
        
        affected_lineups = []
        
        for lineup in self.active_lineups:
            lineup_players = [p['player_key'] for p in lineup['players']]
            if player_name in lineup_players:
                affected_lineups.append(lineup.get('lineup_id', 'unknown'))
        
        return affected_lineups
    
    def _evaluate_leverage_addition(self, player_name: str, ownership_pct: float):
        """Evaluate adding a leverage player to lineups"""
        
        # In production, this would check if we can swap this player into any lineups
        # while maintaining salary cap and position requirements
        
        logger.info(f" Evaluating leverage addition: {player_name} ({ownership_pct:.1%})")
        
        # For now, just log the opportunity
        self._log_integration_event(
            event_type='leverage_opportunity',
            trigger='ownership_drop',
            details=f"{player_name} became leverage play at {ownership_pct:.1%}"
        )
    
    def _system_health_check(self):
        """Check health of all subsystems"""
        
        # Check late swap system
        late_swap_active = self.late_swap_master.monitor.monitoring
        
        # Check ownership tracking
        ownership_active = (self.ownership_tracker and 
                          self.ownership_tracker.tracking_active)
        
        # Log status periodically
        current_time = datetime.now()
        if current_time.minute % 15 == 0:  # Every 15 minutes
            logger.info(f" SYSTEM HEALTH: Late Swap: {'SUCCESS:' if late_swap_active else 'ERROR:'} | "
                       f"Ownership: {'SUCCESS:' if ownership_active else 'ERROR:'} | "
                       f"Players: {len(self.target_players)} | "
                       f"Events: {len(self.integration_events)}")
    
    def _log_integration_event(self, event_type: str, trigger: str, details: str):
        """Log integration events for analysis"""
        
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'trigger': trigger,
            'details': details
        }
        
        self.integration_events.append(event)
        
        logger.info(f" INTEGRATION EVENT: {event_type} | {trigger} | {details}")
    
    def run_pre_lock_optimization(self, minutes_to_lock: int):
        """Run final optimization before lineups lock"""
        
        logger.info("TIME: RUNNING PRE-LOCK OPTIMIZATION")
        logger.info("=" * 50)
        logger.info(f" Time to lock: {minutes_to_lock} minutes")
        
        optimization_results = {
            'timestamp': datetime.now(),
            'minutes_to_lock': minutes_to_lock,
            'actions_taken': [],
            'recommendations': []
        }
        
        # Get late swap analysis
        late_swap_analysis = self.late_swap_master.run_pre_lock_analysis(minutes_to_lock)
        
        # Get ownership pivot recommendations
        ownership_pivots = []
        if self.ownership_tracker:
            ownership_pivots = self.ownership_tracker.get_pivot_recommendations()
        
        # Get final ownership projections
        if self.ownership_tracker and self.ownership_tracker.current_ownership:
            first_contest = list(self.ownership_tracker.current_ownership.keys())[0]
            current_ownership = self.ownership_tracker.current_ownership[first_contest]
            
            # Predict final ownership
            final_projections = self.ownership_tracker.analyzer.predict_final_ownership(
                current_ownership, minutes_to_lock
            )
            
            logger.info("DATA: FINAL OWNERSHIP PROJECTIONS:")
            for player in self.target_players[:5]:  # Show top 5
                if player in final_projections:
                    proj = final_projections[player]
                    logger.info(f"   {player}: {proj['current']:.1%}  {proj['projected_final']:.1%} "
                               f"({proj['projected_change']:+.1%})")
        
        # Generate final recommendations
        recommendations = self._generate_final_recommendations(
            late_swap_analysis, ownership_pivots, minutes_to_lock
        )
        
        optimization_results['recommendations'] = recommendations
        
        # Log final summary
        logger.info(f"INFO: FINAL RECOMMENDATIONS ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:5], 1):
            logger.info(f"   {i}. {rec['action']}: {rec['details']}")
        
        return optimization_results
    
    def _generate_final_recommendations(self, late_swap_analysis: Dict, 
                                      ownership_pivots: List[Dict], 
                                      minutes_to_lock: int) -> List[Dict]:
        """Generate final recommendations before lock"""
        
        recommendations = []
        
        # Late swap recommendations
        if late_swap_analysis.get('recent_updates'):
            for update in late_swap_analysis['recent_updates']:
                if update.severity >= 4:
                    recommendations.append({
                        'priority': 'HIGH',
                        'action': 'Emergency Swap',
                        'details': f"Replace {update.player_name} due to {update.new_status}",
                        'deadline': 'IMMEDIATE'
                    })
        
        # Ownership pivot recommendations
        for pivot in ownership_pivots:
            if pivot['severity'] == 'High':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'action': 'Fade Chalk',
                    'details': f"Consider fading {pivot['fade_player']} ({pivot['current_ownership']:.1%})",
                    'deadline': f"{minutes_to_lock} minutes"
                })
        
        # Time-based recommendations
        if minutes_to_lock <= 30:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Final Check',
                'details': 'Last chance for lineup modifications',
                'deadline': '30 minutes'
            })
        
        return recommendations
    
    def generate_session_report(self) -> Dict:
        """Generate comprehensive session report"""
        
        logger.info("DATA: GENERATING SESSION REPORT")
        logger.info("=" * 50)
        
        # Get data from subsystems
        late_swap_summary = {
            'swaps_executed': len(self.late_swap_master.optimizer.swap_history),
            'player_updates': len(self.late_swap_master.monitor.player_updates),
            'backup_players_generated': len(self.late_swap_master.optimizer.backup_players)
        }
        
        ownership_summary = {}
        if self.ownership_tracker:
            ownership_summary = {
                'alerts_generated': len(self.ownership_tracker.alert_system.alerts_generated),
                'contests_tracked': len(self.ownership_tracker.contest_ids),
                'tracking_duration': 'Active session'
            }
        
        integration_summary = {
            'integration_events': len(self.integration_events),
            'emergency_swaps': len([e for e in self.integration_events if e['event_type'] == 'emergency_swap']),
            'fade_recommendations': len([e for e in self.integration_events if e['event_type'] == 'fade_recommendation']),
            'leverage_opportunities': len([e for e in self.integration_events if e['event_type'] == 'leverage_opportunity'])
        }
        
        report = {
            'session_start': datetime.now(),  # Would track actual start time
            'lineups_managed': len(self.active_lineups),
            'players_monitored': len(self.target_players),
            'contests_tracked': len(self.contest_ids),
            'late_swap_summary': late_swap_summary,
            'ownership_summary': ownership_summary,
            'integration_summary': integration_summary,
            'system_status': 'Active' if self.system_active else 'Stopped'
        }
        
        # Log report summary
        logger.info(f"PROGRESS: SESSION SUMMARY:")
        logger.info(f"   Lineups Managed: {report['lineups_managed']}")
        logger.info(f"   Players Monitored: {report['players_monitored']}")
        logger.info(f"   Swaps Executed: {late_swap_summary['swaps_executed']}")
        logger.info(f"   Ownership Alerts: {ownership_summary.get('alerts_generated', 0)}")
        logger.info(f"   Integration Events: {integration_summary['integration_events']}")
        
        return report
    
    def shutdown_system(self):
        """Shutdown the complete integrated system"""
        
        logger.info(" SHUTTING DOWN INTEGRATED DFS SYSTEM")
        logger.info("=" * 50)
        
        # Generate final report
        final_report = self.generate_session_report()
        
        # Shutdown subsystems
        self.late_swap_master.shutdown_system()
        
        if self.ownership_tracker:
            self.ownership_tracker.stop_tracking()
        
        # Stop integration monitoring
        self.system_active = False
        
        logger.info("SUCCESS: INTEGRATED SYSTEM SHUTDOWN COMPLETE")
        logger.info("DATA: All session data preserved for analysis")
        
        return final_report

def main():
    """Demo the integrated system"""
    
    try:
        # Load data
        projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        ownership = pd.read_csv("../data/advanced_ownership_projections_20250814_134826.csv")
        
        logger.info(f"SUCCESS: Loaded {len(projections)} projections and {len(ownership)} ownership records")
        
        # Create sample lineups
        sample_lineups = [
            {
                'lineup_id': 'tournament_1',
                'players': [
                    {'player_key': 'Shane Bieber', 'Position': 'P', 'Salary': 9200, 'enhanced_fppg': 58.0},
                    {'player_key': 'Cal Raleigh', 'Position': 'C', 'Salary': 4500, 'enhanced_fppg': 14.2},
                    {'player_key': 'Luke Keaschall', 'Position': '2B', 'Salary': 3300, 'enhanced_fppg': 20.3},
                    {'player_key': 'Byron Buxton', 'Position': 'OF', 'Salary': 3900, 'enhanced_fppg': 19.6},
                    {'player_key': 'Juan Soto', 'Position': 'OF', 'Salary': 4200, 'enhanced_fppg': 18.3}
                    # Would have full 9-player lineup
                ]
            },
            {
                'lineup_id': 'tournament_2', 
                'players': [
                    {'player_key': 'River Ryan', 'Position': 'P', 'Salary': 5500, 'enhanced_fppg': 28.0},
                    {'player_key': 'Shea Langeliers', 'Position': 'C', 'Salary': 3500, 'enhanced_fppg': 12.1},
                    # ... more players
                ]
            }
        ]
        
        # Initialize integrated system
        optimizer = IntegratedDFSOptimizer(projections, ownership)
        
        contest_ids = ['main_event_123', 'satellite_456']
        optimizer.initialize_complete_system(sample_lineups, contest_ids)
        
        # Simulate running until 1 hour before lock
        logger.info("TIME: Simulating system operation for 90 seconds...")
        time.sleep(90)
        
        # Run pre-lock optimization
        optimization_results = optimizer.run_pre_lock_optimization(minutes_to_lock=60)
        
        # Wait a bit more
        time.sleep(30)
        
        # Shutdown system
        final_report = optimizer.shutdown_system()
        
        logger.info("COMPLETE: INTEGRATED DFS SYSTEM DEMO COMPLETE!")
        logger.info("START: Your system is now equipped with professional-grade late swap and ownership monitoring!")
        
    except Exception as e:
        logger.error(f"ERROR: Error in integrated system demo: {str(e)}")
        raise

if __name__ == "__main__":
    main()

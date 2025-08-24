#!/usr/bin/env python3
"""
LIVE OWNERSHIP TRACKER
Real-time ownership monitoring with contest analysis and pivot alerts
"""

import pandas as pd
import numpy as np
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import threading
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OwnershipAlert:
    """Ownership change alert"""
    player_name: str
    position: str
    old_ownership: float
    new_ownership: float
    change_pct: float
    alert_type: str  # 'chalk_rising', 'leverage_falling', 'pivot_opportunity'
    severity: int  # 1-5
    timestamp: datetime
    recommendation: str

class ContestAnalyzer:
    """Analyze contest entry patterns and ownership trends"""
    
    def __init__(self):
        self.contest_data = {}
        self.ownership_history = {}
        
    def analyze_contest_fills(self, contest_id: str) -> Dict:
        """Analyze how a contest is filling and ownership patterns"""
        
        # In production, this would connect to FanDuel/DraftKings APIs
        # For demo, we'll simulate contest analysis
        
        fill_rate = np.random.uniform(0.3, 0.8)  # 30-80% filled
        entry_velocity = np.random.uniform(50, 200)  # Entries per minute
        
        # Simulate ownership concentration
        ownership_patterns = {
            'chalk_heavy': np.random.uniform(0.15, 0.25),
            'balanced': np.random.uniform(0.25, 0.35),
            'contrarian_friendly': np.random.uniform(0.35, 0.45)
        }
        
        pattern_type = np.random.choice(list(ownership_patterns.keys()))
        max_ownership = ownership_patterns[pattern_type]
        
        analysis = {
            'contest_id': contest_id,
            'fill_rate': fill_rate,
            'entry_velocity': entry_velocity,
            'ownership_pattern': pattern_type,
            'max_projected_ownership': max_ownership,
            'chalk_concentration': 'High' if max_ownership < 0.25 else 'Medium' if max_ownership < 0.35 else 'Low',
            'contrarian_opportunity': 'High' if max_ownership > 0.4 else 'Medium' if max_ownership > 0.3 else 'Low'
        }
        
        logger.info(f"DATA: CONTEST ANALYSIS - {contest_id}")
        logger.info(f"   Fill Rate: {fill_rate:.1%}")
        logger.info(f"   Entry Velocity: {entry_velocity:.0f}/min")
        logger.info(f"   Pattern: {pattern_type}")
        logger.info(f"   Max Ownership: {max_ownership:.1%}")
        logger.info(f"   Contrarian Opportunity: {analysis['contrarian_opportunity']}")
        
        return analysis
    
    def predict_final_ownership(self, current_ownership: Dict, time_to_lock: int) -> Dict:
        """Predict final ownership based on current trends"""
        
        predictions = {}
        
        for player, current_pct in current_ownership.items():
            
            # Simulate ownership velocity (change per hour)
            velocity = np.random.uniform(-0.05, 0.08)  # -5% to +8% per hour
            
            # Account for diminishing returns and ceiling effects
            if current_pct > 0.3:
                velocity *= 0.5  # Slow growth for high-owned players
            elif current_pct < 0.05:
                velocity *= 1.5  # Faster growth for low-owned players
            
            # Project to lock time
            hours_to_lock = time_to_lock / 60.0
            projected_change = velocity * hours_to_lock
            
            final_ownership = max(0.01, min(0.6, current_pct + projected_change))
            
            predictions[player] = {
                'current': current_pct,
                'velocity': velocity,
                'projected_final': final_ownership,
                'projected_change': projected_change,
                'confidence': np.random.uniform(0.6, 0.9)
            }
        
        return predictions

class LiveOwnershipAPI:
    """Interface for live ownership data (simulated)"""
    
    def __init__(self):
        self.api_endpoints = {
            'fanduel': 'https://api.fanduel.com/contests/{contest_id}/entries',
            'draftkings': 'https://api.draftkings.com/contests/{contest_id}/lineups',
            'superdraft': 'https://api.superdraft.com/contests/{contest_id}/ownership'
        }
        
        # Base ownership for simulation
        self.base_ownership = {
            'Shane Bieber': 0.45,
            'Garrett Crochet': 0.42,
            'Chris Sale': 0.38,
            'Hunter Brown': 0.35,
            'Cal Raleigh': 0.03,
            'River Ryan': 0.08,
            'Luke Keaschall': 0.06,
            'Shea Langeliers': 0.02,
            'Byron Buxton': 0.12,
            'Juan Soto': 0.15
        }
        
    def get_live_ownership(self, contest_id: str, platform: str = 'fanduel') -> Dict:
        """Get current ownership percentages from platform"""
        
        # In production, this would make API calls to DFS platforms
        # For demo, we'll simulate realistic ownership changes
        
        current_ownership = {}
        
        for player, base_pct in self.base_ownership.items():
            
            # Add realistic variance (5%)
            variance = np.random.uniform(-0.05, 0.05)
            current_pct = max(0.01, min(0.6, base_pct + variance))
            
            current_ownership[player] = current_pct
        
        # Simulate some dramatic changes occasionally
        if np.random.random() < 0.2:  # 20% chance
            
            # Simulate news-driven ownership change
            affected_player = np.random.choice(list(current_ownership.keys()))
            
            if 'injury' in str(np.random.choice(['news', 'injury', 'lineup'])):
                # Simulate injury news dropping ownership
                current_ownership[affected_player] *= 0.6
                logger.warning(f" SIMULATED NEWS IMPACT: {affected_player} ownership dropped")
            else:
                # Simulate positive news increasing ownership
                current_ownership[affected_player] *= 1.3
                logger.info(f"PROGRESS: SIMULATED NEWS IMPACT: {affected_player} ownership increased")
        
        return current_ownership
    
    def get_entry_distribution(self, contest_id: str) -> Dict:
        """Get distribution of entries by ownership ranges"""
        
        # Simulate entry distribution analysis
        distribution = {
            'unique_lineups': np.random.randint(15000, 45000),
            'duplicate_lineups': np.random.randint(5000, 15000),
            'ownership_ranges': {
                'low_owned_heavy': np.random.uniform(0.15, 0.25),   # % of lineups with avg <10% ownership
                'balanced': np.random.uniform(0.40, 0.60),          # % of lineups with avg 10-20% ownership  
                'chalk_heavy': np.random.uniform(0.15, 0.35)        # % of lineups with avg >20% ownership
            },
            'stack_popularity': {
                'HOU': np.random.uniform(0.12, 0.18),
                'LAD': np.random.uniform(0.10, 0.16),
                'ATL': np.random.uniform(0.08, 0.14),
                'BOS': np.random.uniform(0.06, 0.12)
            }
        }
        
        return distribution

class OwnershipAlertSystem:
    """Generate and manage ownership alerts"""
    
    def __init__(self, ownership_thresholds: Dict = None):
        self.thresholds = ownership_thresholds or {
            'chalk_alert': 0.25,      # Alert when player hits 25%+ ownership
            'fade_threshold': 0.35,    # Consider fading at 35%+
            'leverage_alert': 0.05,    # Alert when good player drops below 5%
            'pivot_opportunity': 0.15  # Look for pivots when chalk rises above 15%
        }
        
        self.alerts_generated = []
        self.player_targets = {}
        
    def set_player_targets(self, lineup_players: List[str]):
        """Set target players to monitor from your lineups"""
        
        self.player_targets = {player: True for player in lineup_players}
        logger.info(f"TARGET: Monitoring {len(lineup_players)} players for ownership alerts")
        
    def analyze_ownership_changes(self, current_ownership: Dict, 
                                previous_ownership: Dict) -> List[OwnershipAlert]:
        """Analyze ownership changes and generate alerts"""
        
        alerts = []
        
        for player, current_pct in current_ownership.items():
            
            previous_pct = previous_ownership.get(player, current_pct)
            change = current_pct - previous_pct
            change_pct = (change / previous_pct) * 100 if previous_pct > 0 else 0
            
            # Skip if change is too small
            if abs(change) < 0.01:  # Less than 1% change
                continue
                
            alert = None
            
            # Chalk rising alert
            if (current_pct > self.thresholds['chalk_alert'] and 
                change > 0.02 and player in self.player_targets):
                
                alert = OwnershipAlert(
                    player_name=player,
                    position='TBD',  # Would get from player data
                    old_ownership=previous_pct,
                    new_ownership=current_pct,
                    change_pct=change_pct,
                    alert_type='chalk_rising',
                    severity=4 if current_pct > self.thresholds['fade_threshold'] else 3,
                    timestamp=datetime.now(),
                    recommendation=f"Consider fading - now {current_pct:.1%} owned (+{change:.1%})"
                )
            
            # Leverage opportunity alert
            elif (current_pct < self.thresholds['leverage_alert'] and 
                  change < -0.01 and previous_pct > 0.08):
                
                alert = OwnershipAlert(
                    player_name=player,
                    position='TBD',
                    old_ownership=previous_pct,
                    new_ownership=current_pct,
                    change_pct=change_pct,
                    alert_type='leverage_falling',
                    severity=5,  # High priority for leverage opportunities
                    timestamp=datetime.now(),
                    recommendation=f"LEVERAGE OPPORTUNITY - dropped to {current_pct:.1%} owned ({change:.1%})"
                )
            
            # Pivot opportunity alert
            elif (self.thresholds['pivot_opportunity'] < current_pct < self.thresholds['chalk_alert'] and
                  change > 0.03):
                
                alert = OwnershipAlert(
                    player_name=player,
                    position='TBD',
                    old_ownership=previous_pct,
                    new_ownership=current_pct,
                    change_pct=change_pct,
                    alert_type='pivot_opportunity',
                    severity=2,
                    timestamp=datetime.now(),
                    recommendation=f"Pivot candidate - rising to {current_pct:.1%} owned (+{change:.1%})"
                )
            
            if alert:
                alerts.append(alert)
                self.alerts_generated.append(alert)
                
                # Log the alert
                severity_emoji = "" if alert.severity >= 4 else "WARNING:" if alert.severity >= 3 else "TIP:"
                logger.warning(f"{severity_emoji} {alert.alert_type.upper()}: {alert.player_name}")
                logger.warning(f"   {alert.old_ownership:.1%}  {alert.new_ownership:.1%} ({change_pct:+.1f}%)")
                logger.warning(f"   {alert.recommendation}")
        
        return alerts
    
    def get_active_alerts(self, minutes: int = 30) -> List[OwnershipAlert]:
        """Get alerts from the last N minutes"""
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [alert for alert in self.alerts_generated if alert.timestamp > cutoff]

class RealTimeOwnershipTracker:
    """Main class for real-time ownership tracking"""
    
    def __init__(self, target_players: List[str]):
        self.api = LiveOwnershipAPI()
        self.analyzer = ContestAnalyzer()
        self.alert_system = OwnershipAlertSystem()
        
        self.target_players = target_players
        self.tracking_active = False
        self.ownership_history = {}
        self.current_ownership = {}
        
        # Set up alert monitoring
        self.alert_system.set_player_targets(target_players)
        
    def start_tracking(self, contest_ids: List[str], check_interval: int = 300):
        """Start real-time ownership tracking"""
        
        logger.info("DATA: STARTING REAL-TIME OWNERSHIP TRACKING")
        logger.info("=" * 60)
        
        self.contest_ids = contest_ids
        self.check_interval = check_interval
        self.tracking_active = True
        
        logger.info(f"TARGET: Tracking {len(self.target_players)} players")
        logger.info(f"INFO: Monitoring {len(contest_ids)} contests")
        logger.info(f" Check interval: {check_interval} seconds")
        
        # Start tracking thread
        threading.Thread(target=self._tracking_loop, daemon=True).start()
        
        # Analyze initial contest state
        for contest_id in contest_ids:
            self.analyzer.analyze_contest_fills(contest_id)
    
    def _tracking_loop(self):
        """Main tracking loop"""
        
        iteration = 0
        
        while self.tracking_active:
            try:
                iteration += 1
                logger.info(f"SWAP: Ownership check #{iteration} at {datetime.now().strftime('%H:%M:%S')}")
                
                # Get current ownership for all contests
                for contest_id in self.contest_ids:
                    
                    # Get live ownership data
                    new_ownership = self.api.get_live_ownership(contest_id)
                    
                    # Store previous ownership for comparison
                    previous_ownership = self.current_ownership.get(contest_id, {})
                    self.current_ownership[contest_id] = new_ownership
                    
                    # Generate alerts for significant changes
                    if previous_ownership:
                        alerts = self.alert_system.analyze_ownership_changes(
                            new_ownership, previous_ownership
                        )
                        
                        if alerts:
                            logger.info(f" Generated {len(alerts)} ownership alerts for {contest_id}")
                    
                    # Update ownership history
                    timestamp = datetime.now()
                    if contest_id not in self.ownership_history:
                        self.ownership_history[contest_id] = {}
                    
                    for player, ownership_pct in new_ownership.items():
                        if player not in self.ownership_history[contest_id]:
                            self.ownership_history[contest_id][player] = []
                        
                        self.ownership_history[contest_id][player].append({
                            'timestamp': timestamp,
                            'ownership': ownership_pct
                        })
                
                # Log current state summary
                self._log_ownership_summary()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"ERROR: Error in ownership tracking: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _log_ownership_summary(self):
        """Log current ownership summary"""
        
        if not self.current_ownership:
            return
            
        # Get first contest for summary (would aggregate across contests in production)
        first_contest = list(self.current_ownership.keys())[0]
        ownership_data = self.current_ownership[first_contest]
        
        # Sort by ownership for display
        sorted_ownership = sorted(ownership_data.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("DATA: CURRENT OWNERSHIP SUMMARY:")
        
        for player, ownership_pct in sorted_ownership[:10]:  # Top 10
            if player in self.target_players:
                status = "TARGET: [TARGET]"
            elif ownership_pct > 0.3:
                status = " [CHALK]"
            elif ownership_pct < 0.05:
                status = " [LEVERAGE]"
            else:
                status = "PROGRESS: [MEDIUM]"
                
            logger.info(f"   {player}: {ownership_pct:.1%} {status}")
    
    def get_ownership_trends(self, player: str, contest_id: str = None) -> Dict:
        """Get ownership trends for a specific player"""
        
        if contest_id is None:
            contest_id = list(self.ownership_history.keys())[0]
            
        if (contest_id not in self.ownership_history or 
            player not in self.ownership_history[contest_id]):
            return {}
        
        history = self.ownership_history[contest_id][player]
        
        if len(history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate trend
        recent_ownership = [h['ownership'] for h in history[-5:]]  # Last 5 data points
        trend_slope = np.polyfit(range(len(recent_ownership)), recent_ownership, 1)[0]
        
        current_ownership = history[-1]['ownership']
        peak_ownership = max(h['ownership'] for h in history)
        
        return {
            'player': player,
            'current_ownership': current_ownership,
            'peak_ownership': peak_ownership,
            'trend_direction': 'rising' if trend_slope > 0.001 else 'falling' if trend_slope < -0.001 else 'stable',
            'trend_strength': abs(trend_slope),
            'data_points': len(history),
            'tracking_duration': (history[-1]['timestamp'] - history[0]['timestamp']).total_seconds() / 60
        }
    
    def get_pivot_recommendations(self, ownership_threshold: float = 0.25) -> List[Dict]:
        """Get pivot recommendations based on current ownership"""
        
        recommendations = []
        
        if not self.current_ownership:
            return recommendations
        
        # Use first contest for analysis
        first_contest = list(self.current_ownership.keys())[0]
        ownership_data = self.current_ownership[first_contest]
        
        # Find high-owned players in our targets
        for player in self.target_players:
            if player in ownership_data:
                ownership_pct = ownership_data[player]
                
                if ownership_pct > ownership_threshold:
                    # Find similar lower-owned alternatives
                    # This would use your player database in production
                    pivot_options = self._find_pivot_options(player, ownership_data)
                    
                    recommendations.append({
                        'fade_player': player,
                        'current_ownership': ownership_pct,
                        'pivot_options': pivot_options,
                        'severity': 'High' if ownership_pct > 0.35 else 'Medium',
                        'recommendation': f"Consider fading {player} ({ownership_pct:.1%}) for lower-owned alternatives"
                    })
        
        return recommendations
    
    def _find_pivot_options(self, player: str, ownership_data: Dict) -> List[Dict]:
        """Find pivot options for a high-owned player"""
        
        # Simulate finding pivot options
        # In production, this would query your player database
        
        pivot_options = []
        
        if 'Bieber' in player:
            pivot_options = [
                {'player': 'River Ryan', 'ownership': ownership_data.get('River Ryan', 0.08), 'reason': 'Similar upside, much lower owned'},
                {'player': 'AJ Blubaugh', 'ownership': ownership_data.get('AJ Blubaugh', 0.06), 'reason': 'Value option with decent floor'}
            ]
        elif 'Crochet' in player:
            pivot_options = [
                {'player': 'Braxton Garrett', 'ownership': ownership_data.get('Braxton Garrett', 0.04), 'reason': 'Solid matchup, contrarian play'},
                {'player': 'Luis Ortiz', 'ownership': ownership_data.get('Luis Ortiz', 0.03), 'reason': 'High ceiling if he hits'}
            ]
        
        return pivot_options
    
    def generate_final_report(self) -> Dict:
        """Generate final ownership report before lineups lock"""
        
        logger.info("INFO: GENERATING FINAL OWNERSHIP REPORT")
        logger.info("=" * 50)
        
        # Get active alerts
        active_alerts = self.alert_system.get_active_alerts(minutes=60)
        
        # Get pivot recommendations
        pivot_recs = self.get_pivot_recommendations()
        
        # Analyze trends for target players
        player_trends = {}
        if self.current_ownership:
            first_contest = list(self.current_ownership.keys())[0]
            for player in self.target_players:
                trends = self.get_ownership_trends(player, first_contest)
                if trends:
                    player_trends[player] = trends
        
        report = {
            'timestamp': datetime.now(),
            'contests_monitored': len(self.contest_ids),
            'players_tracked': len(self.target_players),
            'active_alerts': len(active_alerts),
            'pivot_recommendations': len(pivot_recs),
            'player_trends': player_trends,
            'alerts': active_alerts,
            'pivots': pivot_recs
        }
        
        # Log summary
        logger.info(f"TARGET: Tracked {len(self.target_players)} players across {len(self.contest_ids)} contests")
        logger.info(f" Generated {len(active_alerts)} alerts in last hour")
        logger.info(f"SWAP: Found {len(pivot_recs)} pivot opportunities")
        
        if active_alerts:
            logger.info(" RECENT ALERTS:")
            for alert in active_alerts[-3:]:  # Show last 3
                logger.info(f"    {alert.player_name}: {alert.recommendation}")
        
        if pivot_recs:
            logger.info("SWAP: PIVOT RECOMMENDATIONS:")
            for rec in pivot_recs:
                logger.info(f"    Fade {rec['fade_player']} ({rec['current_ownership']:.1%})")
        
        return report
    
    def stop_tracking(self):
        """Stop ownership tracking"""
        
        self.tracking_active = False
        
        # Generate final report
        final_report = self.generate_final_report()
        
        logger.info("SUCCESS: OWNERSHIP TRACKING STOPPED")
        logger.info("DATA: Final tracking session complete")

def main():
    """Demo the live ownership tracking system"""
    
    try:
        # Define target players from your lineups
        target_players = [
            'Shane Bieber', 'Garrett Crochet', 'Chris Sale', 'Hunter Brown',
            'Cal Raleigh', 'River Ryan', 'Luke Keaschall', 'Byron Buxton', 'Juan Soto'
        ]
        
        # Initialize tracker
        tracker = RealTimeOwnershipTracker(target_players)
        
        # Start tracking
        contest_ids = ['contest_123', 'contest_456']
        tracker.start_tracking(contest_ids, check_interval=10)  # 10 seconds for demo
        
        # Run for demo period
        logger.info("TIME: Running ownership tracking demo for 60 seconds...")
        time.sleep(60)
        
        # Stop tracking and get final report
        tracker.stop_tracking()
        
        logger.info("COMPLETE: LIVE OWNERSHIP TRACKING DEMO COMPLETE!")
        
    except Exception as e:
        logger.error(f"ERROR: Error in ownership tracking demo: {str(e)}")
        raise

if __name__ == "__main__":
    main()

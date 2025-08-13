#!/usr/bin/env python3
"""
REAL-TIME FEATURE UPDATE SYSTEM
==============================

Continuously updates player features throughout the day:
- Lineup changes and batting order updates
- Injury report monitoring  
- Weather condition updates
- Line movement tracking
- Sharp money indicators

This ensures your predictions stay current as conditions change.
"""

import pandas as pd
import numpy as np
import requests
import json
import logging
from datetime import datetime, timedelta
import time
import os
from threading import Timer
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeFeatureUpdater:
    def __init__(self):
        self.last_update = {}
        self.lineup_changes = []
        self.injury_updates = []
        self.weather_updates = {}
        self.line_movements = []
        
    def check_lineup_changes(self):
        """Monitor for lineup changes throughout the day"""
        logger.info("👥 Checking for lineup changes...")
        
        try:
            # Load today's expected lineups
            confirmed_starters_file = "../data/confirmed_starters_today.csv"
            if os.path.exists(confirmed_starters_file):
                current_lineups = pd.read_csv(confirmed_starters_file)
                
                # Compare with previous lineups (if available)
                previous_file = "../data/previous_lineups.csv"
                if os.path.exists(previous_file):
                    previous_lineups = pd.read_csv(previous_file)
                    
                    # Find changes
                    changes = self.detect_lineup_changes(current_lineups, previous_lineups)
                    
                    if changes:
                        logger.info(f"🚨 {len(changes)} lineup changes detected!")
                        for change in changes:
                            logger.info(f"   {change}")
                            self.lineup_changes.append({
                                'timestamp': datetime.now(),
                                'change': change
                            })
                        
                        # Update predictions for affected players
                        self.update_affected_predictions(changes)
                
                # Save current lineups as previous for next check
                current_lineups.to_csv(previous_file, index=False)
                
            else:
                logger.warning("❌ No confirmed starters file found")
                
        except Exception as e:
            logger.error(f"❌ Error checking lineup changes: {e}")
    
    def detect_lineup_changes(self, current_df, previous_df):
        """Detect specific lineup changes"""
        changes = []
        
        # Check for new players
        current_players = set(current_df['Name'].values)
        previous_players = set(previous_df['Name'].values)
        
        new_players = current_players - previous_players
        removed_players = previous_players - current_players
        
        for player in new_players:
            team = current_df[current_df['Name'] == player]['Team'].iloc[0]
            changes.append(f"NEW STARTER: {player} ({team})")
        
        for player in removed_players:
            team = previous_df[previous_df['Name'] == player]['Team'].iloc[0]
            changes.append(f"REMOVED: {player} ({team}) - likely injury/rest")
        
        # Check for batting order changes
        for _, current_row in current_df.iterrows():
            player = current_row['Name']
            current_order = current_row.get('Batting_Order', 0)
            
            previous_row = previous_df[previous_df['Name'] == player]
            if not previous_row.empty:
                previous_order = previous_row.iloc[0].get('Batting_Order', 0)
                
                if current_order != previous_order and current_order > 0 and previous_order > 0:
                    changes.append(f"BATTING ORDER CHANGE: {player} ({previous_order} → {current_order})")
        
        return changes
    
    def monitor_injury_reports(self):
        """Check for injury report updates"""
        logger.info("🏥 Checking injury reports...")
        
        try:
            # This would integrate with MLB injury report APIs
            # For now, simulate checking for common injury indicators
            
            # Check for "DTD" (day-to-day) or "Questionable" players
            confirmed_file = "../data/confirmed_starters_today.csv"
            if os.path.exists(confirmed_file):
                df = pd.read_csv(confirmed_file)
                
                # Look for injury status indicators
                questionable_players = []
                
                for _, player in df.iterrows():
                    player_name = player['Name']
                    
                    # Check for status indicators
                    status = player.get('Status', '').upper()
                    if any(keyword in status for keyword in ['DTD', 'QUESTIONABLE', 'PROBABLE']):
                        questionable_players.append({
                            'player': player_name,
                            'team': player.get('Team', 'UNK'),
                            'status': status
                        })
                
                if questionable_players:
                    logger.info(f"⚠️ {len(questionable_players)} players with injury concerns:")
                    for player_info in questionable_players:
                        logger.info(f"   {player_info['player']} ({player_info['team']}) - {player_info['status']}")
                        
                        # Adjust prediction confidence for questionable players
                        self.adjust_for_injury_risk(player_info)
                
        except Exception as e:
            logger.error(f"❌ Error checking injury reports: {e}")
    
    def update_weather_conditions(self):
        """Update weather conditions for all games"""
        logger.info("🌤️ Updating weather conditions...")
        
        try:
            # Load enhanced weather analytics
            from enhanced_weather_analytics import EnhancedWeatherAnalytics
            weather_analytics = EnhancedWeatherAnalytics()
            
            # Get current games
            confirmed_file = "../data/confirmed_starters_today.csv"
            if os.path.exists(confirmed_file):
                df = pd.read_csv(confirmed_file)
                teams = df['Team'].unique()
                
                weather_updates = {}
                significant_changes = []
                
                for team in teams:
                    current_weather = weather_analytics.get_weather_data(team)
                    
                    # Compare with previous weather (if available)
                    if team in self.weather_updates:
                        prev_weather = self.weather_updates[team]
                        
                        # Check for significant changes
                        temp_change = abs(current_weather['temperature'] - prev_weather['temperature'])
                        wind_change = abs(current_weather['wind_speed'] - prev_weather['wind_speed'])
                        
                        if temp_change > 10:  # 10+ degree change
                            significant_changes.append(f"{team}: Temperature changed by {temp_change:.0f}°F")
                        
                        if wind_change > 5:  # 5+ mph wind change
                            significant_changes.append(f"{team}: Wind changed by {wind_change:.0f} mph")
                    
                    weather_updates[team] = current_weather
                
                if significant_changes:
                    logger.info("🌪️ Significant weather changes detected:")
                    for change in significant_changes:
                        logger.info(f"   {change}")
                    
                    # Regenerate weather-enhanced predictions
                    self.regenerate_weather_predictions()
                
                self.weather_updates = weather_updates
                
        except Exception as e:
            logger.error(f"❌ Error updating weather: {e}")
    
    def track_line_movements(self):
        """Monitor sportsbook line movements"""
        logger.info("📈 Tracking line movements...")
        
        try:
            # Load current PrizePicks lines
            current_pp_file = "../data/PrizePicks_MLB.xlsx"
            if os.path.exists(current_pp_file):
                current_lines = pd.read_excel(current_pp_file)
                
                # Compare with previous lines
                prev_lines_file = "../data/previous_prizepicks_lines.xlsx"
                if os.path.exists(prev_lines_file):
                    prev_lines = pd.read_excel(prev_lines_file)
                    
                    line_changes = self.detect_line_movements(current_lines, prev_lines)
                    
                    if line_changes:
                        logger.info(f"📊 {len(line_changes)} line movements detected:")
                        for change in line_changes:
                            logger.info(f"   {change}")
                            
                            # Track sharp money indicators
                            if 'increased' in change.lower():
                                self.line_movements.append({
                                    'timestamp': datetime.now(),
                                    'change': change,
                                    'direction': 'up',
                                    'sharp_money_indicator': True
                                })
                
                # Save current lines for next comparison
                current_lines.to_excel(prev_lines_file, index=False)
                
        except Exception as e:
            logger.error(f"❌ Error tracking line movements: {e}")
    
    def detect_line_movements(self, current_df, prev_df):
        """Detect significant line movements"""
        movements = []
        
        for _, current_row in current_df.iterrows():
            player = current_row.get('player_name', '')
            
            # Find matching previous player
            prev_row = prev_df[prev_df.get('player_name', '') == player]
            if prev_row.empty:
                continue
            
            prev_row = prev_row.iloc[0]
            
            # Check each stat for line changes
            stats_to_check = ['Hits', 'Home Runs', 'Total Bases', 'RBIs', 'Runs Scored']
            
            for stat in stats_to_check:
                if stat in current_row.index and stat in prev_row.index:
                    current_line = current_row[stat]
                    prev_line = prev_row[stat]
                    
                    if pd.notna(current_line) and pd.notna(prev_line):
                        if current_line != prev_line:
                            change_amount = current_line - prev_line
                            direction = "increased" if change_amount > 0 else "decreased"
                            movements.append(
                                f"{player} {stat}: {prev_line} → {current_line} ({direction} by {abs(change_amount)})"
                            )
        
        return movements
    
    def adjust_for_injury_risk(self, player_info):
        """Adjust predictions for injury risk"""
        player_name = player_info['player']
        status = player_info['status']
        
        # Load current predictions
        try:
            predictions_file = "../data/weather_enhanced_predictions_latest.csv"
            if os.path.exists(predictions_file):
                df = pd.read_csv(predictions_file)
                
                # Find matching player
                player_row = df[df['player_name'].str.contains(player_name, case=False, na=False)]
                
                if not player_row.empty:
                    idx = player_row.index[0]
                    
                    # Apply injury risk adjustments
                    risk_factor = 0.85 if 'QUESTIONABLE' in status else 0.95
                    
                    # Adjust predictions downward for injury risk
                    stat_columns = [col for col in df.columns if '_prediction' in col]
                    for col in stat_columns:
                        if pd.notna(df.loc[idx, col]):
                            df.loc[idx, col] *= risk_factor
                    
                    # Add injury risk flag
                    df.loc[idx, 'injury_risk'] = status
                    
                    # Save updated predictions
                    df.to_csv(predictions_file, index=False)
                    
                    logger.info(f"🏥 Adjusted predictions for {player_name} (injury risk: {status})")
                    
        except Exception as e:
            logger.error(f"❌ Error adjusting for injury risk: {e}")
    
    def regenerate_weather_predictions(self):
        """Regenerate predictions with updated weather"""
        logger.info("🔄 Regenerating weather-enhanced predictions...")
        
        try:
            # Run the weather analytics script
            os.system("python enhanced_weather_analytics.py")
            logger.info("✅ Weather predictions regenerated")
            
        except Exception as e:
            logger.error(f"❌ Error regenerating weather predictions: {e}")
    
    def update_affected_predictions(self, lineup_changes):
        """Update predictions for players affected by lineup changes"""
        logger.info("🔄 Updating predictions for lineup changes...")
        
        try:
            # For significant lineup changes, regenerate predictions
            significant_changes = [change for change in lineup_changes if 
                                 'NEW STARTER' in change or 'BATTING ORDER' in change]
            
            if significant_changes:
                logger.info("🔄 Significant changes detected - regenerating all predictions")
                os.system("python enhanced_automated_betting_system.py")
                logger.info("✅ Predictions updated for lineup changes")
                
        except Exception as e:
            logger.error(f"❌ Error updating predictions: {e}")
    
    def run_update_cycle(self):
        """Run complete update cycle"""
        logger.info("🔄 Running real-time update cycle...")
        
        try:
            # Check all real-time factors
            self.check_lineup_changes()
            self.monitor_injury_reports()
            self.update_weather_conditions()
            self.track_line_movements()
            
            # Generate summary
            self.generate_update_summary()
            
            logger.info("✅ Update cycle completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in update cycle: {e}")
    
    def generate_update_summary(self):
        """Generate summary of all updates"""
        logger.info("\n📋 REAL-TIME UPDATE SUMMARY")
        logger.info("=" * 30)
        
        logger.info(f"🕐 Update time: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"👥 Lineup changes tracked: {len(self.lineup_changes)}")
        logger.info(f"🏥 Injury updates: {len(self.injury_updates)}")
        logger.info(f"🌤️ Weather updates: {len(self.weather_updates)} teams")
        logger.info(f"📊 Line movements: {len(self.line_movements)}")
        
        # Save summary to file
        summary = {
            'timestamp': datetime.now().isoformat(),
            'lineup_changes': len(self.lineup_changes),
            'injury_updates': len(self.injury_updates),
            'weather_updates': len(self.weather_updates),
            'line_movements': len(self.line_movements),
            'recent_changes': self.lineup_changes[-5:] if self.lineup_changes else []
        }
        
        with open("../data/realtime_update_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)

def run_continuous_updates(update_interval_minutes=30):
    """Run continuous updates throughout the day"""
    logger.info(f"🚀 Starting continuous real-time updates (every {update_interval_minutes} minutes)")
    
    updater = RealTimeFeatureUpdater()
    
    def scheduled_update():
        updater.run_update_cycle()
        
        # Schedule next update
        timer = Timer(update_interval_minutes * 60, scheduled_update)
        timer.daemon = True
        timer.start()
    
    # Run initial update
    updater.run_update_cycle()
    
    # Start scheduled updates
    scheduled_update()
    
    try:
        # Keep running
        while True:
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("🛑 Real-time updates stopped by user")

def main():
    """Main real-time updater execution"""
    print("🔄 REAL-TIME FEATURE UPDATE SYSTEM")
    print("=" * 40)
    
    updater = RealTimeFeatureUpdater()
    
    # Check command line arguments
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Run continuous updates
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        run_continuous_updates(interval)
    else:
        # Run single update cycle
        print("Running single update cycle...")
        updater.run_update_cycle()
        print("\n✅ Single update cycle completed")
        print("💡 Use --continuous [minutes] for ongoing updates")

if __name__ == "__main__":
    main()

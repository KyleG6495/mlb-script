#!/usr/bin/env python3
"""
Injury & News Sentiment Analyzer - Monitor player status and news impact

This enhancement:
- Tracks injury reports and return dates
- Analyzes news sentiment around players
- Adjusts predictions based on recent news
- Monitors lineup changes and rest days
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import re

class InjuryNewsAnalyzer:
    def __init__(self):
        self.injury_keywords = [
            'injured', 'injury', 'IL', 'disabled list', 'day-to-day', 'DTD',
            'sore', 'strain', 'sprain', 'surgery', 'rehab', 'questionable'
        ]
        
        self.positive_keywords = [
            'healthy', 'cleared', 'activated', 'return', 'back', 'ready',
            'feeling good', 'full strength', 'no issues'
        ]
        
        self.rest_keywords = [
            'rest day', 'day off', 'scheduled rest', 'maintenance day'
        ]
    
    def get_player_news(self, player_name):
        """Get recent news for a specific player"""
        try:
            # Example RSS/API feed scraping
            # In practice, you'd use sports news APIs like:
            # - ESPN API
            # - MLB.com RSS feeds
            # - RotoBaller API
            # - FantasyLabs API
            
            # Simulated news data
            sample_news = [
                {
                    'headline': f"{player_name} dealing with minor shoulder soreness",
                    'date': datetime.now() - timedelta(days=1),
                    'source': 'ESPN',
                    'content': f"Manager says {player_name} is day-to-day with shoulder soreness but expected to play."
                },
                {
                    'headline': f"{player_name} hits two home runs in return from IL",
                    'date': datetime.now() - timedelta(days=2),
                    'source': 'MLB.com',
                    'content': f"{player_name} looked healthy in first game back, going 3-for-4 with 2 HR."
                }
            ]
            
            return sample_news
            
        except Exception as e:
            print(f"WARNING: Error getting news for {player_name}: {e}")
            return []
    
    def analyze_news_sentiment(self, news_items):
        """Analyze sentiment and injury status from news"""
        sentiment_score = 0
        injury_concerns = []
        positive_signals = []
        
        for news in news_items:
            text = (news['headline'] + ' ' + news['content']).lower()
            
            # Check for injury keywords
            for keyword in self.injury_keywords:
                if keyword in text:
                    injury_concerns.append(keyword)
                    sentiment_score -= 1
            
            # Check for positive keywords
            for keyword in self.positive_keywords:
                if keyword in text:
                    positive_signals.append(keyword)
                    sentiment_score += 1
            
            # Check for rest days
            for keyword in self.rest_keywords:
                if keyword in text:
                    sentiment_score -= 0.5  # Minor negative
        
        return {
            'sentiment_score': sentiment_score,
            'injury_concerns': injury_concerns,
            'positive_signals': positive_signals,
            'overall_status': self.get_status_from_score(sentiment_score)
        }
    
    def get_status_from_score(self, score):
        """Convert sentiment score to status"""
        if score >= 2:
            return "VERY_POSITIVE"
        elif score >= 1:
            return "POSITIVE"
        elif score >= -1:
            return "NEUTRAL"
        elif score >= -2:
            return "CONCERNING"
        else:
            return "HIGH_RISK"
    
    def get_prediction_adjustment(self, sentiment_analysis):
        """Calculate prediction adjustment based on news sentiment"""
        score = sentiment_analysis['sentiment_score']
        status = sentiment_analysis['overall_status']
        
        # Adjustment multipliers
        adjustments = {
            'VERY_POSITIVE': 1.15,  # 15% boost
            'POSITIVE': 1.08,       # 8% boost
            'NEUTRAL': 1.00,        # No change
            'CONCERNING': 0.92,     # 8% reduction
            'HIGH_RISK': 0.80       # 20% reduction
        }
        
        return adjustments.get(status, 1.00)
    
    def analyze_lineup_changes(self, todays_slate, historical_lineups):
        """Detect unusual lineup changes that might indicate issues"""
        lineup_alerts = []
        
        for _, player in todays_slate.iterrows():
            player_name = player['Nickname']
            position = player['Position']
            batting_order = player.get('Batting Order', None)
            
            # Check for unusual batting order changes
            if pd.notna(batting_order):
                usual_spot = self.get_usual_batting_spot(player_name, historical_lineups)
                
                if usual_spot and abs(batting_order - usual_spot) >= 3:
                    lineup_alerts.append({
                        'player': player_name,
                        'alert_type': 'BATTING_ORDER_CHANGE',
                        'usual_spot': usual_spot,
                        'todays_spot': batting_order,
                        'impact': 'NEGATIVE' if batting_order > usual_spot else 'POSITIVE'
                    })
        
        return lineup_alerts
    
    def get_usual_batting_spot(self, player_name, historical_lineups):
        """Get player's usual batting order position"""
        # Simplified - in practice you'd analyze historical data
        # Common batting order by player type
        typical_spots = {
            'leadoff_types': 1,
            'contact_hitters': 2,
            'power_hitters': 3,
            'cleanup_hitters': 4,
            'rbi_guys': 5
        }
        
        # Return a simulated usual spot
        return 3  # Most players bat 3rd typically
    
    def enhance_predictions_with_news(self, predictions_df):
        """Apply news-based adjustments to predictions"""
        
        print(" ANALYZING PLAYER NEWS & INJURY STATUS")
        print("=" * 50)
        
        enhanced_predictions = predictions_df.copy()
        news_analysis = []
        
        for _, player in predictions_df.iterrows():
            player_name = player['name'] if 'name' in player.index else player.get('player', 'Unknown')
            
            # Get news for this player
            news_items = self.get_player_news(player_name)
            
            if news_items:
                # Analyze sentiment
                sentiment = self.analyze_news_sentiment(news_items)
                adjustment = self.get_prediction_adjustment(sentiment)
                
                print(f"DATA: {player_name}: {sentiment['overall_status']} ({adjustment:.0%})")
                
                # Apply adjustment to all stats
                stats_to_adjust = ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']
                for stat in stats_to_adjust:
                    if stat in enhanced_predictions.columns:
                        enhanced_predictions.at[player.name, stat] *= adjustment
                
                # Store analysis
                news_analysis.append({
                    'player': player_name,
                    'sentiment_score': sentiment['sentiment_score'],
                    'status': sentiment['overall_status'],
                    'adjustment': adjustment,
                    'concerns': sentiment['injury_concerns'],
                    'positives': sentiment['positive_signals']
                })
        
        # Add news analysis to dataframe
        enhanced_predictions['news_adjustment'] = [
            next((na['adjustment'] for na in news_analysis if na['player'] == name), 1.0)
            for name in enhanced_predictions.get('name', enhanced_predictions.index)
        ]
        
        return enhanced_predictions, news_analysis
    
    def generate_injury_alerts(self, news_analysis):
        """Generate alerts for players with injury concerns"""
        
        alerts = []
        
        for analysis in news_analysis:
            if analysis['status'] in ['CONCERNING', 'HIGH_RISK']:
                alerts.append({
                    'player': analysis['player'],
                    'risk_level': analysis['status'],
                    'concerns': analysis['concerns'],
                    'recommendation': 'AVOID' if analysis['status'] == 'HIGH_RISK' else 'REDUCE_EXPOSURE'
                })
        
        return alerts

def main():
    analyzer = InjuryNewsAnalyzer()
    
    # Sample predictions data
    sample_predictions = pd.DataFrame({
        'name': ['Aaron Judge', 'Shohei Ohtani', 'Ronald Acuna Jr.'],
        'hits': [1.8, 1.9, 2.0],
        'home_runs': [0.6, 0.8, 0.4],
        'total_bases': [3.2, 3.5, 3.1]
    })
    
    enhanced_preds, news_analysis = analyzer.enhance_predictions_with_news(sample_predictions)
    alerts = analyzer.generate_injury_alerts(news_analysis)
    
    print(f"\n INJURY/NEWS ALERTS:")
    for alert in alerts:
        print(f"WARNING: {alert['player']}: {alert['risk_level']}")
        print(f"   Recommendation: {alert['recommendation']}")
        print(f"   Concerns: {', '.join(alert['concerns'])}")
        print()

if __name__ == "__main__":
    main()

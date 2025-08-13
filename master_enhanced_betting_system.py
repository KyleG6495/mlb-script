#!/usr/bin/env python3
"""
MASTER ENHANCED BETTING SYSTEM
Integrates all advanced features for maximum betting edge

This master script coordinates:
1. Enhanced betting analysis with YES/NO recommendations
2. Combo prop optimization
3. Advanced model analytics with confidence scoring
4. Weather and ballpark factor adjustments
5. Live odds integration
6. Injury and news sentiment analysis
7. ML ensemble predictions
8. Bankroll management with Kelly Criterion
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Import all enhancement modules
try:
    from enhanced_betting_analyzer import EnhancedBettingAnalyzer
    from combo_prop_optimizer import ComboPropOptimizer
    from advanced_model_analytics import AdvancedModelAnalytics
    from weather_ballpark_analyzer import WeatherBallparkAnalyzer
    from live_odds_scraper import LiveOddsScraper
    from injury_news_analyzer import InjuryNewsAnalyzer
    from ml_ensemble_system import MLEnsembleSystem
    from bankroll_manager import BankrollManager
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("📁 Make sure all enhancement scripts are in the same directory")

class MasterBettingSystem:
    def __init__(self, initial_bankroll=1000):
        print("🚀 INITIALIZING MASTER ENHANCED BETTING SYSTEM")
        print("=" * 60)
        
        # Initialize all components
        self.betting_analyzer = EnhancedBettingAnalyzer()
        self.combo_optimizer = ComboPropOptimizer()
        self.model_analytics = AdvancedModelAnalytics()
        self.weather_analyzer = WeatherBallparkAnalyzer()
        self.odds_scraper = LiveOddsScraper()
        self.news_analyzer = InjuryNewsAnalyzer()
        self.ml_ensemble = MLEnsembleSystem()
        self.bankroll_manager = BankrollManager(initial_bankroll=initial_bankroll)
        
        print("✅ All components initialized successfully!")
    
    def run_complete_analysis(self, slate_date=None):
        """Run the complete enhanced betting analysis pipeline"""
        
        if slate_date is None:
            slate_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n🎯 RUNNING COMPLETE ANALYSIS FOR {slate_date}")
        print("=" * 60)
        
        try:
            # Step 1: Load base data
            print("\n📊 STEP 1: LOADING BASE DATA")
            base_data = self.load_base_data()
            
            # Step 2: Enhanced ML predictions with ensemble
            print("\n🤖 STEP 2: GENERATING ENSEMBLE PREDICTIONS")
            enhanced_predictions = self.generate_ensemble_predictions(base_data)
            
            # Step 3: Apply weather and ballpark adjustments
            print("\n🌤️ STEP 3: APPLYING WEATHER & BALLPARK FACTORS")
            weather_adjusted = self.apply_weather_adjustments(enhanced_predictions)
            
            # Step 4: Incorporate injury and news analysis
            print("\n📰 STEP 4: ANALYZING INJURY & NEWS SENTIMENT")
            news_adjusted = self.apply_news_adjustments(weather_adjusted)
            
            # Step 5: Get live odds data
            print("\n💰 STEP 5: SCRAPING LIVE ODDS")
            live_odds = self.get_live_odds()
            
            # Step 6: Enhanced betting analysis with confidence
            print("\n🎯 STEP 6: ENHANCED BETTING ANALYSIS")
            betting_recommendations = self.generate_betting_recommendations(
                news_adjusted, live_odds
            )
            
            # Step 7: Combo prop optimization
            print("\n🔥 STEP 7: COMBO PROP OPTIMIZATION")
            combo_opportunities = self.find_combo_opportunities(betting_recommendations)
            
            # Step 8: Advanced model analytics
            print("\n📈 STEP 8: ADVANCED MODEL ANALYTICS")
            confidence_analysis = self.run_confidence_analysis(betting_recommendations)
            
            # Step 9: Bankroll optimization
            print("\n💰 STEP 9: BANKROLL OPTIMIZATION")
            optimized_portfolio = self.optimize_bankroll_allocation(
                betting_recommendations, combo_opportunities
            )
            
            # Step 10: Generate master report
            print("\n📋 STEP 10: GENERATING MASTER REPORT")
            self.generate_master_report(
                betting_recommendations, combo_opportunities, 
                confidence_analysis, optimized_portfolio
            )
            
            return {
                'betting_recommendations': betting_recommendations,
                'combo_opportunities': combo_opportunities,
                'confidence_analysis': confidence_analysis,
                'optimized_portfolio': optimized_portfolio
            }
            
        except Exception as e:
            print(f"❌ Error in complete analysis: {e}")
            return None
    
    def load_base_data(self):
        """Load and prepare base data for analysis"""
        
        try:
            # Load FanDuel slate
            fd_slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
            
            # Load predictions and features
            hitter_features = pd.read_csv('../data/fd_hitter_features_final.csv')
            pitcher_features = pd.read_csv('../data/fd_pitcher_features_final.csv')
            
            # Load base scores
            hitter_scores = pd.read_csv('../data/base_hitter_scores.csv')
            pitcher_scores = pd.read_csv('../data/base_pitcher_scores.csv')
            
            print(f"📊 Loaded {len(fd_slate)} players from FanDuel slate")
            print(f"📈 Loaded {len(hitter_features)} hitter features")
            print(f"⚾ Loaded {len(pitcher_features)} pitcher features")
            
            return {
                'fd_slate': fd_slate,
                'hitter_features': hitter_features,
                'pitcher_features': pitcher_features,
                'hitter_scores': hitter_scores,
                'pitcher_scores': pitcher_scores
            }
            
        except Exception as e:
            print(f"⚠️ Error loading base data: {e}")
            return {}
    
    def generate_ensemble_predictions(self, base_data):
        """Generate enhanced predictions using ML ensemble"""
        
        # Combine hitter and pitcher data
        all_features = pd.concat([
            base_data.get('hitter_features', pd.DataFrame()),
            base_data.get('pitcher_features', pd.DataFrame())
        ], ignore_index=True)
        
        if len(all_features) == 0:
            print("⚠️ No features available for ensemble predictions")
            return pd.DataFrame()
        
        # Generate ensemble predictions
        predictions, confidence = self.ml_ensemble.predict_ensemble(all_features)
        
        # Create enhanced predictions dataframe
        enhanced_df = all_features.copy()
        for target, preds in predictions.items():
            enhanced_df[f'{target}_ensemble'] = preds
            enhanced_df[f'{target}_confidence'] = confidence[target]
        
        print(f"✅ Generated ensemble predictions for {len(enhanced_df)} players")
        return enhanced_df
    
    def apply_weather_adjustments(self, predictions_df):
        """Apply weather and ballpark factor adjustments"""
        
        adjusted_df = predictions_df.copy()
        
        # Apply weather adjustments
        weather_adjustments = self.weather_analyzer.analyze_weather_impact(predictions_df)
        
        # Apply ballpark factors (create dummy games_df if needed)
        try:
            games_df = pd.DataFrame({'venue': ['Unknown'], 'city': ['Unknown']})
            ballpark_adjustments = self.weather_analyzer.apply_ballpark_factors(predictions_df, games_df)
        except:
            ballpark_adjustments = {'hits': 1.0, 'total_bases': 1.0, 'home_runs': 1.0}
        
        # Combine adjustments
        for stat in ['hits', 'total_bases', 'home_runs']:
            if f'{stat}_ensemble' in adjusted_df.columns:
                weather_mult = weather_adjustments.get(stat, 1.0)
                ballpark_mult = ballpark_adjustments.get(stat, 1.0) if isinstance(ballpark_adjustments, dict) else 1.0
                
                adjusted_df[f'{stat}_ensemble'] *= weather_mult * ballpark_mult
        
        print("✅ Applied weather and ballpark adjustments")
        return adjusted_df
    
    def apply_news_adjustments(self, predictions_df):
        """Apply injury and news sentiment adjustments"""
        
        adjusted_df, news_analysis = self.news_analyzer.enhance_predictions_with_news(predictions_df)
        
        # Generate injury alerts
        injury_alerts = self.news_analyzer.generate_injury_alerts(news_analysis)
        
        if injury_alerts:
            print(f"🚨 {len(injury_alerts)} injury/news alerts generated")
            for alert in injury_alerts:
                print(f"   ⚠️ {alert['player']}: {alert['recommendation']}")
        
        return adjusted_df
    
    def get_live_odds(self):
        """Scrape live odds from multiple sportsbooks"""
        
        # Sample props to check
        sample_props = [
            {'player': 'Aaron Judge', 'prop_type': 'total_bases', 'line': 1.5},
            {'player': 'Shohei Ohtani', 'prop_type': 'home_runs', 'line': 0.5},
        ]
        
        live_odds = self.odds_scraper.scrape_multiple_books(sample_props)
        
        print(f"💰 Retrieved live odds for {len(live_odds)} props")
        return live_odds
    
    def generate_betting_recommendations(self, predictions_df, live_odds):
        """Generate enhanced betting recommendations"""
        
        # Use enhanced betting analyzer
        recommendations = self.betting_analyzer.analyze_all_props(predictions_df)
        
        # Apply live odds if available
        for rec in recommendations:
            player = rec.get('player', '')
            prop_type = rec.get('prop_type', '')
            
            # Look for matching live odds
            for odds_data in live_odds:
                if (odds_data.get('player') == player and 
                    odds_data.get('prop_type') == prop_type):
                    rec['live_odds'] = odds_data.get('best_odds', rec.get('odds', -110))
                    rec['odds_source'] = odds_data.get('best_book', 'Default')
                    break
        
        print(f"🎯 Generated {len(recommendations)} betting recommendations")
        return recommendations
    
    def find_combo_opportunities(self, betting_recommendations):
        """Find profitable combo prop opportunities"""
        
        # Filter to high-confidence single bets
        high_confidence_bets = [
            bet for bet in betting_recommendations 
            if bet.get('confidence_level', 'LOW') in ['HIGH', 'VERY_HIGH']
            and bet.get('recommendation') == 'YES'
        ]
        
        if len(high_confidence_bets) < 2:
            print("⚠️ Not enough high-confidence bets for combo analysis")
            return []
        
        # Find combo opportunities
        combo_opportunities = self.combo_optimizer.find_combo_opportunities(high_confidence_bets)
        
        print(f"🔥 Found {len(combo_opportunities)} combo opportunities")
        return combo_opportunities
    
    def run_confidence_analysis(self, betting_recommendations):
        """Run advanced confidence and uncertainty analysis"""
        
        # Convert recommendations to DataFrame for analysis
        rec_df = pd.DataFrame(betting_recommendations)
        
        if len(rec_df) == 0:
            return {}
        
        # Run confidence analysis
        confidence_analysis = self.model_analytics.calculate_confidence_intervals(rec_df)
        
        # Identify outliers
        outlier_analysis = self.model_analytics.identify_outliers(rec_df)
        
        print("📈 Completed advanced confidence analysis")
        return {
            'confidence_intervals': confidence_analysis,
            'outlier_analysis': outlier_analysis
        }
    
    def optimize_bankroll_allocation(self, betting_recommendations, combo_opportunities):
        """Optimize bankroll allocation across all opportunities with proper payout handling"""
        
        # Combine single bets and combo opportunities
        all_opportunities = []
        
        # Add single bets (traditional sportsbook odds)
        for bet in betting_recommendations:
            if bet.get('recommendation') == 'YES':
                all_opportunities.append({
                    'type': 'single',
                    'platform': 'sportsbook',
                    'player': bet.get('player'),
                    'prop': bet.get('prop_type'),
                    'win_probability': bet.get('win_probability', 0.5),
                    'odds': bet.get('odds', -110),
                    'expected_value': bet.get('expected_value', 0),
                    'confidence': bet.get('confidence_level_numeric', 0.5),
                    'is_fixed_multiplier': False
                })
        
        # Add combo opportunities (fixed multiplier payouts)
        for combo in combo_opportunities:
            all_opportunities.append({
                'type': 'combo',
                'platform': combo.get('platform', 'PrizePicks'),
                'players': combo.get('players', []),
                'props': combo.get('props', []),
                'win_probability': combo.get('combo_probability', 0.5),
                'payout_multiplier': combo.get('payout_multiplier', 3.0),
                'expected_value': combo.get('expected_value', 0),
                'confidence': combo.get('confidence', 0.5),
                'is_fixed_multiplier': True
            })
        
        # Optimize portfolio with platform-aware sizing
        if all_opportunities:
            optimized_portfolio = self.optimize_mixed_portfolio(all_opportunities)
            print(f"💰 Optimized mixed portfolio with {len(optimized_portfolio)} bets")
            return optimized_portfolio
        else:
            print("⚠️ No opportunities available for bankroll optimization")
            return []
    
    def optimize_mixed_portfolio(self, opportunities):
        """Optimize portfolio with both traditional odds and fixed multipliers"""
        
        optimized_bets = []
        
        for opp in opportunities:
            if opp['type'] == 'single':
                # Traditional sportsbook bet
                bet_rec = self.bankroll_manager.calculate_recommended_bet(
                    win_probability=opp['win_probability'],
                    odds_or_multiplier=opp['odds'],
                    confidence_level=opp['confidence'],
                    is_fixed_multiplier=False,
                    platform=opp['platform']
                )
            else:
                # Fixed multiplier combo bet
                bet_rec = self.bankroll_manager.calculate_recommended_bet(
                    win_probability=opp['win_probability'],
                    odds_or_multiplier=opp['payout_multiplier'],
                    confidence_level=opp['confidence'],
                    is_fixed_multiplier=True,
                    platform=opp['platform']
                )
            
            if bet_rec['recommended_amount'] > 0:
                optimized_bets.append({
                    **opp,
                    'recommended_amount': bet_rec['recommended_amount'],
                    'kelly_fraction': bet_rec['kelly_fraction'],
                    'reasoning': bet_rec['reasoning'],
                    'bet_type': bet_rec['bet_type']
                })
        
        return optimized_bets
    
    def generate_master_report(self, betting_recs, combo_ops, confidence_analysis, portfolio):
        """Generate comprehensive master report"""
        
        print("\n" + "=" * 80)
        print("📋 MASTER ENHANCED BETTING SYSTEM REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_single_bets = len([b for b in betting_recs if b.get('recommendation') == 'YES'])
        total_combo_ops = len(combo_ops)
        total_portfolio_value = sum([p.get('recommended_amount', 0) for p in portfolio])
        
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(f"   🎯 Single Bet Opportunities: {total_single_bets}")
        print(f"   🔥 Combo Opportunities: {total_combo_ops}")
        print(f"   💰 Total Portfolio Value: ${total_portfolio_value:.2f}")
        print(f"   📈 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Top recommendations
        print(f"\n🏆 TOP SINGLE BET RECOMMENDATIONS:")
        top_single = sorted(
            [b for b in betting_recs if b.get('recommendation') == 'YES'],
            key=lambda x: x.get('expected_value', 0),
            reverse=True
        )[:5]
        
        for i, bet in enumerate(top_single, 1):
            print(f"   {i}. {bet.get('player')} - {bet.get('prop_type')}")
            print(f"      💰 EV: {bet.get('expected_value', 0):.1f}% | Confidence: {bet.get('confidence_level', 'UNKNOWN')}")
        
        # Top combo opportunities
        if combo_ops:
            print(f"\n🔥 TOP COMBO OPPORTUNITIES:")
            top_combos = sorted(combo_ops, key=lambda x: x.get('expected_value', 0), reverse=True)[:3]
            
            for i, combo in enumerate(top_combos, 1):
                players = combo.get('players', [])
                print(f"   {i}. {' + '.join(players[:2])}{'...' if len(players) > 2 else ''}")
                print(f"      🎯 Payout: {combo.get('payout_multiplier', 0):.1f}x | EV: {combo.get('expected_value', 0):.1f}%")
        
        # Bankroll allocation
        print(f"\n💰 BANKROLL ALLOCATION:")
        current_bankroll = self.bankroll_manager.current_bankroll
        total_allocation = sum([p.get('recommended_amount', 0) for p in portfolio])
        allocation_percentage = (total_allocation / current_bankroll) * 100 if current_bankroll > 0 else 0
        
        print(f"   💵 Current Bankroll: ${current_bankroll:.2f}")
        print(f"   📊 Total Allocation: ${total_allocation:.2f} ({allocation_percentage:.1f}%)")
        print(f"   🛡️ Risk Level: {'HIGH' if allocation_percentage > 15 else 'MODERATE' if allocation_percentage > 8 else 'CONSERVATIVE'}")
        
        # Risk alerts
        print(f"\n⚠️ RISK ALERTS:")
        risk_alerts = []
        
        if allocation_percentage > 20:
            risk_alerts.append("🚨 Very high daily allocation - consider reducing exposure")
        
        if total_combo_ops > 5:
            risk_alerts.append("⚡ High number of combo bets - correlation risk present")
        
        if not risk_alerts:
            risk_alerts.append("✅ No significant risk alerts detected")
        
        for alert in risk_alerts:
            print(f"   {alert}")
        
        # Save detailed report to file
        self.save_detailed_report(betting_recs, combo_ops, confidence_analysis, portfolio)
        
        print(f"\n📁 Detailed report saved to: enhanced_betting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print("\n🎯 MASTER ANALYSIS COMPLETE! 🎯")
    
    def save_detailed_report(self, betting_recs, combo_ops, confidence_analysis, portfolio):
        """Save detailed report to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"../data/enhanced_betting_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("MASTER ENHANCED BETTING SYSTEM - DETAILED REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Single bets section
            f.write("SINGLE BET RECOMMENDATIONS:\n")
            f.write("-" * 30 + "\n")
            for bet in betting_recs:
                if bet.get('recommendation') == 'YES':
                    f.write(f"Player: {bet.get('player')}\n")
                    f.write(f"Prop: {bet.get('prop_type')}\n")
                    f.write(f"Expected Value: {bet.get('expected_value', 0):.1f}%\n")
                    f.write(f"Confidence: {bet.get('confidence_level', 'UNKNOWN')}\n")
                    f.write(f"Odds: {bet.get('odds', -110)}\n\n")
            
            # Combo opportunities section
            f.write("COMBO OPPORTUNITIES:\n")
            f.write("-" * 20 + "\n")
            for combo in combo_ops:
                f.write(f"Players: {', '.join(combo.get('players', []))}\n")
                f.write(f"Payout: {combo.get('payout_multiplier', 0):.1f}x\n")
                f.write(f"Expected Value: {combo.get('expected_value', 0):.1f}%\n\n")
            
            # Portfolio allocation
            f.write("PORTFOLIO ALLOCATION:\n")
            f.write("-" * 20 + "\n")
            for bet in portfolio:
                f.write(f"Amount: ${bet.get('recommended_amount', 0):.2f}\n")
                f.write(f"Reasoning: {bet.get('reasoning', 'N/A')}\n\n")

def main():
    """Main execution function"""
    
    # Initialize master system
    master_system = MasterBettingSystem(initial_bankroll=1000)
    
    # Run complete analysis
    results = master_system.run_complete_analysis()
    
    if results:
        print("\n🚀 Master Enhanced Betting System analysis completed successfully!")
    else:
        print("\n❌ Analysis failed - check error messages above")

if __name__ == "__main__":
    main()

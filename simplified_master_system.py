#!/usr/bin/env python3
"""
SIMPLIFIED MASTER ENHANCED BETTING SYSTEM
Works with existing data and models

This version coordinates your existing enhanced betting system
with additional features like combo optimization and bankroll management.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

class SimplifiedMasterSystem:
    def __init__(self, initial_bankroll=1000):
        print("START: INITIALIZING SIMPLIFIED MASTER BETTING SYSTEM")
        print("=" * 60)
        
        # Import existing modules if available
        try:
            from enhanced_betting_analyzer import EnhancedBettingAnalyzer
            self.betting_analyzer = EnhancedBettingAnalyzer()
            self.has_enhanced_analyzer = True
        except ImportError:
            print("WARNING: Enhanced betting analyzer not found - using basic analysis")
            self.has_enhanced_analyzer = False
        
        try:
            from combo_prop_optimizer import ComboPropOptimizer
            self.combo_optimizer = ComboPropOptimizer()
            self.has_combo_optimizer = True
        except ImportError:
            print("WARNING: Combo optimizer not found - skipping combo analysis")
            self.has_combo_optimizer = False
        
        try:
            from bankroll_manager import BankrollManager
            self.bankroll_manager = BankrollManager(initial_bankroll=initial_bankroll)
            self.has_bankroll_manager = True
        except ImportError:
            print("WARNING: Bankroll manager not found - using basic bet sizing")
            self.has_bankroll_manager = False
            self.initial_bankroll = initial_bankroll
        
        print("SUCCESS: System initialized with available components!")
    
    def run_analysis(self):
        """Run simplified master analysis using existing data"""
        
        print(f"\nTARGET: RUNNING SIMPLIFIED MASTER ANALYSIS")
        print("=" * 60)
        
        try:
            # Step 1: Load existing data
            print("\nDATA: STEP 1: LOADING EXISTING DATA")
            data = self.load_existing_data()
            
            if not data:
                print("ERROR: No data available for analysis")
                return None
            
            # Step 2: Enhanced betting analysis
            print("\nTARGET: STEP 2: ENHANCED BETTING ANALYSIS")
            betting_recommendations = self.run_enhanced_analysis(data)
            
            # Step 3: Combo optimization (if available)
            combo_opportunities = []
            if self.has_combo_optimizer and betting_recommendations:
                print("\n STEP 3: COMBO PROP OPTIMIZATION")
                combo_opportunities = self.find_combo_opportunities(betting_recommendations)
            
            # Step 4: Bankroll optimization
            print("\nMONEY: STEP 4: BANKROLL OPTIMIZATION")
            portfolio = self.optimize_portfolio(betting_recommendations, combo_opportunities)
            
            # Step 5: Generate comprehensive report
            print("\nINFO: STEP 5: GENERATING MASTER REPORT")
            self.generate_comprehensive_report(betting_recommendations, combo_opportunities, portfolio)
            
            return {
                'betting_recommendations': betting_recommendations,
                'combo_opportunities': combo_opportunities,
                'portfolio': portfolio
            }
            
        except Exception as e:
            print(f"ERROR: Error in analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_existing_data(self):
        """Load existing prediction and feature data"""
        
        data = {}
        
        try:
            # Try to load FanDuel data
            fd_files = [
                '../fd_current_slate/fd_slate_today.csv',
                '../data/fd_hitter_features_final.csv', 
                '../data/base_hitter_scores.csv',
                '../data/fd_dk_hitter_scores.csv'
            ]
            
            for file_path in fd_files:
                try:
                    if 'slate' in file_path:
                        data['fd_slate'] = pd.read_csv(file_path)
                        print(f"DATA: Loaded {len(data['fd_slate'])} players from FanDuel slate")
                    elif 'features' in file_path:
                        data['hitter_features'] = pd.read_csv(file_path)
                        print(f"PROGRESS: Loaded {len(data['hitter_features'])} hitter features")
                    elif 'base_hitter_scores' in file_path:
                        data['base_scores'] = pd.read_csv(file_path)
                        print(f"TARGET: Loaded {len(data['base_scores'])} base predictions")
                    elif 'fd_dk_hitter_scores' in file_path:
                        data['predictions'] = pd.read_csv(file_path)
                        print(f" Loaded {len(data['predictions'])} enhanced predictions")
                except FileNotFoundError:
                    print(f"WARNING: File not found: {file_path}")
                    continue
            
            return data if data else None
            
        except Exception as e:
            print(f"WARNING: Error loading data: {e}")
            return None
    
    def run_enhanced_analysis(self, data):
        """Run enhanced betting analysis on available data"""
        
        if self.has_enhanced_analyzer:
            # Use the enhanced analyzer
            try:
                # Try to use the most complete dataset available
                if 'predictions' in data:
                    predictions_df = data['predictions']
                elif 'base_scores' in data:
                    predictions_df = data['base_scores']
                else:
                    print("WARNING: No prediction data available")
                    return []
                
                recommendations = self.betting_analyzer.analyze_all_props(predictions_df)
                print(f"SUCCESS: Generated {len(recommendations)} betting recommendations")
                return recommendations
                
            except Exception as e:
                print(f"WARNING: Error in enhanced analysis: {e}")
                return self.run_basic_analysis(data)
        else:
            return self.run_basic_analysis(data)
    
    def run_basic_analysis(self, data):
        """Run basic betting analysis if enhanced analyzer unavailable"""
        
        print("DATA: Running basic betting analysis...")
        
        recommendations = []
        
        # Use whatever prediction data is available
        if 'predictions' in data:
            df = data['predictions']
        elif 'base_scores' in data:
            df = data['base_scores']
        else:
            print("WARNING: No prediction data for basic analysis")
            return []
        
        # Basic prop analysis
        for _, player in df.iterrows():
            player_name = player.get('name', player.get('player', 'Unknown'))
            
            # Hits analysis
            if 'hits' in player.index:
                hits_pred = player['hits']
                if hits_pred >= 1.8:  # Strong hit prediction
                    recommendations.append({
                        'player': player_name,
                        'prop_type': 'hits',
                        'line': 1.5,
                        'prediction': hits_pred,
                        'recommendation': 'YES',
                        'confidence_level': 'HIGH' if hits_pred >= 2.0 else 'MEDIUM',
                        'expected_value': (hits_pred - 1.5) * 20,  # Simple EV calc
                        'odds': -110
                    })
            
            # Total bases analysis
            if 'total_bases' in player.index:
                tb_pred = player['total_bases']
                if tb_pred >= 2.2:  # Strong total bases prediction
                    recommendations.append({
                        'player': player_name,
                        'prop_type': 'total_bases',
                        'line': 1.5,
                        'prediction': tb_pred,
                        'recommendation': 'YES',
                        'confidence_level': 'HIGH' if tb_pred >= 2.5 else 'MEDIUM',
                        'expected_value': (tb_pred - 1.5) * 15,
                        'odds': -110
                    })
            
            # Home runs analysis
            if 'home_runs' in player.index:
                hr_pred = player['home_runs']
                if hr_pred >= 0.4:  # Strong HR prediction
                    recommendations.append({
                        'player': player_name,
                        'prop_type': 'home_runs',
                        'line': 0.5,
                        'prediction': hr_pred,
                        'recommendation': 'YES',
                        'confidence_level': 'HIGH' if hr_pred >= 0.6 else 'MEDIUM',
                        'expected_value': (hr_pred - 0.5) * 30,
                        'odds': +150
                    })
        
        print(f"SUCCESS: Generated {len(recommendations)} basic recommendations")
        return recommendations
    
    def find_combo_opportunities(self, betting_recommendations):
        """Find combo opportunities using available optimizer"""
        
        if not self.has_combo_optimizer:
            return []
        
        try:
            # Filter to high-confidence bets
            high_confidence = [
                bet for bet in betting_recommendations 
                if bet.get('confidence_level') in ['HIGH', 'VERY_HIGH']
                and bet.get('recommendation') == 'YES'
            ]
            
            if len(high_confidence) < 2:
                print("WARNING: Not enough high-confidence bets for combos")
                return []
            
            combos = self.combo_optimizer.find_combo_opportunities(high_confidence)
            print(f" Found {len(combos)} combo opportunities")
            return combos
            
        except Exception as e:
            print(f"WARNING: Error in combo optimization: {e}")
            return []
    
    def optimize_portfolio(self, betting_recommendations, combo_opportunities):
        """Optimize bet sizing and portfolio allocation"""
        
        portfolio = []
        
        if self.has_bankroll_manager:
            try:
                # Use sophisticated bankroll management
                all_opportunities = []
                
                # Add single bets
                for bet in betting_recommendations:
                    if bet.get('recommendation') == 'YES':
                        all_opportunities.append({
                            'type': 'single',
                            'player': bet.get('player'),
                            'prop': bet.get('prop_type'),
                            'win_probability': min(0.8, max(0.4, bet.get('prediction', 0.5) / 2)),
                            'odds': bet.get('odds', -110),
                            'expected_value': bet.get('expected_value', 0),
                            'confidence': 0.8 if bet.get('confidence_level') == 'HIGH' else 0.6
                        })
                
                # Add combos
                for combo in combo_opportunities:
                    all_opportunities.append({
                        'type': 'combo',
                        'players': combo.get('players', []),
                        'win_probability': combo.get('combo_probability', 0.3),
                        'odds': combo.get('payout_odds', 300),
                        'expected_value': combo.get('expected_value', 0),
                        'confidence': combo.get('confidence', 0.5)
                    })
                
                portfolio = self.bankroll_manager.optimize_bet_portfolio(all_opportunities)
                
            except Exception as e:
                print(f"WARNING: Error in bankroll optimization: {e}")
                portfolio = self.simple_portfolio_optimization(betting_recommendations, combo_opportunities)
        else:
            portfolio = self.simple_portfolio_optimization(betting_recommendations, combo_opportunities)
        
        return portfolio
    
    def simple_portfolio_optimization(self, betting_recommendations, combo_opportunities):
        """Simple portfolio optimization without bankroll manager"""
        
        portfolio = []
        max_single_bet = self.initial_bankroll * 0.05  # 5% max per bet
        
        # Add single bets with simple sizing
        yes_bets = [bet for bet in betting_recommendations if bet.get('recommendation') == 'YES']
        yes_bets.sort(key=lambda x: x.get('expected_value', 0), reverse=True)
        
        for bet in yes_bets[:10]:  # Top 10 bets
            confidence = bet.get('confidence_level', 'MEDIUM')
            if confidence == 'HIGH':
                bet_size = max_single_bet
            else:
                bet_size = max_single_bet * 0.5
            
            portfolio.append({
                **bet,
                'recommended_amount': bet_size,
                'reasoning': f"Simple sizing based on {confidence} confidence"
            })
        
        # Add top combo if available
        if combo_opportunities:
            top_combo = max(combo_opportunities, key=lambda x: x.get('expected_value', 0))
            portfolio.append({
                **top_combo,
                'recommended_amount': max_single_bet * 0.3,  # Smaller for combos
                'reasoning': "Top combo opportunity with reduced sizing"
            })
        
        print(f"MONEY: Created simple portfolio with {len(portfolio)} bets")
        return portfolio
    
    def generate_comprehensive_report(self, betting_recommendations, combo_opportunities, portfolio):
        """Generate comprehensive master report"""
        
        print("\n" + "=" * 80)
        print("INFO: SIMPLIFIED MASTER BETTING SYSTEM REPORT")
        print("=" * 80)
        
        # Summary stats
        yes_bets = [b for b in betting_recommendations if b.get('recommendation') == 'YES']
        total_allocation = sum([p.get('recommended_amount', 0) for p in portfolio])
        
        print(f"\nDATA: EXECUTIVE SUMMARY:")
        print(f"   TARGET: Total Opportunities: {len(betting_recommendations)}")
        print(f"   SUCCESS: YES Recommendations: {len(yes_bets)}")
        print(f"    Combo Opportunities: {len(combo_opportunities)}")
        print(f"   MONEY: Total Portfolio Value: ${total_allocation:.2f}")
        print(f"   PROGRESS: Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Top single bets
        print(f"\nLINEUP: TOP SINGLE BET RECOMMENDATIONS:")
        top_bets = sorted(yes_bets, key=lambda x: x.get('expected_value', 0), reverse=True)[:5]
        
        for i, bet in enumerate(top_bets, 1):
            print(f"   {i}. {bet.get('player', 'Unknown')} - {bet.get('prop_type', 'Unknown')}")
            print(f"      MONEY: EV: {bet.get('expected_value', 0):.1f}% | Confidence: {bet.get('confidence_level', 'UNKNOWN')}")
            print(f"      TARGET: Prediction: {bet.get('prediction', 0):.2f} | Line: {bet.get('line', 'N/A')}")
        
        # Top combos
        if combo_opportunities:
            print(f"\n TOP COMBO OPPORTUNITIES:")
            top_combos = sorted(combo_opportunities, key=lambda x: x.get('expected_value', 0), reverse=True)[:3]
            
            for i, combo in enumerate(top_combos, 1):
                players = combo.get('players', [])
                print(f"   {i}. {' + '.join(players[:2])}{'...' if len(players) > 2 else ''}")
                print(f"      TARGET: Payout: {combo.get('payout_multiplier', 0):.1f}x | EV: {combo.get('expected_value', 0):.1f}%")
        
        # Portfolio allocation
        print(f"\nMONEY: PORTFOLIO ALLOCATION:")
        bankroll = getattr(self, 'current_bankroll', self.initial_bankroll) if hasattr(self, 'bankroll_manager') else self.initial_bankroll
        allocation_pct = (total_allocation / bankroll) * 100 if bankroll > 0 else 0
        
        print(f"    Available Bankroll: ${bankroll:.2f}")
        print(f"   DATA: Total Allocation: ${total_allocation:.2f} ({allocation_pct:.1f}%)")
        print(f"    Risk Level: {'HIGH' if allocation_pct > 15 else 'MODERATE' if allocation_pct > 8 else 'CONSERVATIVE'}")
        
        # Save report
        self.save_report(betting_recommendations, combo_opportunities, portfolio)
        
        print(f"\n Report saved to: simplified_master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print("\nTARGET: SIMPLIFIED MASTER ANALYSIS COMPLETE! TARGET:")
    
    def save_report(self, betting_recs, combo_ops, portfolio):
        """Save detailed report to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"../data/simplified_master_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("SIMPLIFIED MASTER BETTING SYSTEM REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # YES recommendations
                f.write("YES BET RECOMMENDATIONS:\n")
                f.write("-" * 25 + "\n")
                yes_bets = [b for b in betting_recs if b.get('recommendation') == 'YES']
                for bet in yes_bets:
                    f.write(f"Player: {bet.get('player', 'Unknown')}\n")
                    f.write(f"Prop: {bet.get('prop_type', 'Unknown')}\n")
                    f.write(f"Prediction: {bet.get('prediction', 0):.2f}\n")
                    f.write(f"Line: {bet.get('line', 'N/A')}\n")
                    f.write(f"Expected Value: {bet.get('expected_value', 0):.1f}%\n")
                    f.write(f"Confidence: {bet.get('confidence_level', 'UNKNOWN')}\n\n")
                
                # Combo opportunities
                if combo_ops:
                    f.write("COMBO OPPORTUNITIES:\n")
                    f.write("-" * 20 + "\n")
                    for combo in combo_ops:
                        f.write(f"Players: {', '.join(combo.get('players', []))}\n")
                        f.write(f"Payout: {combo.get('payout_multiplier', 0):.1f}x\n")
                        f.write(f"Expected Value: {combo.get('expected_value', 0):.1f}%\n\n")
                
                # Portfolio
                f.write("PORTFOLIO ALLOCATION:\n")
                f.write("-" * 20 + "\n")
                for bet in portfolio:
                    f.write(f"Bet: {bet.get('player', 'Combo')} - {bet.get('prop_type', 'Multiple')}\n")
                    f.write(f"Amount: ${bet.get('recommended_amount', 0):.2f}\n")
                    f.write(f"Reasoning: {bet.get('reasoning', 'N/A')}\n\n")
                    
        except Exception as e:
            print(f"WARNING: Error saving report: {e}")

def main():
    """Main execution function"""
    
    # Initialize simplified system
    system = SimplifiedMasterSystem(initial_bankroll=1000)
    
    # Run analysis
    results = system.run_analysis()
    
    if results:
        print("\nSTART: Simplified Master System completed successfully!")
        print("TARGET: Check the generated report for betting recommendations!")
    else:
        print("\nERROR: Analysis failed - check error messages above")

if __name__ == "__main__":
    main()

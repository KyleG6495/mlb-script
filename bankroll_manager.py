#!/usr/bin/env python3
"""
Bankroll Management & Kelly Criterion Calculator

This enhancement:
- Implements Kelly Criterion for optimal bet sizing
- Tracks win/loss streaks and adjusts accordingly
- Manages risk across multiple bets
- Provides portfolio optimization for prop bets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class BankrollManager:
    def __init__(self, initial_bankroll=1000, max_bet_percentage=0.25, kelly_multiplier=0.25):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.max_bet_percentage = max_bet_percentage
        self.kelly_multiplier = kelly_multiplier  # Fractional Kelly for safety
        
        self.bet_history = []
        self.daily_results = []
        self.current_exposure = 0
        
        # Risk management parameters
        self.max_daily_risk = 0.10  # Never risk more than 10% per day
        self.stop_loss_trigger = 0.20  # Reduce bet sizes after 20% loss
        self.winning_streak_bonus = 0.05  # Small bonus during win streaks
        
    def calculate_kelly_bet_size(self, win_probability, odds_or_multiplier, is_fixed_multiplier=False):
        """Calculate optimal bet size using Kelly Criterion for both traditional odds and fixed multipliers"""
        
        if is_fixed_multiplier:
            # For fixed multipliers (PrizePicks/Underdog): payout = multiplier * bet_amount
            # Kelly formula: f = (p * multiplier - 1) / (multiplier - 1)
            multiplier = odds_or_multiplier
            p = win_probability
            
            kelly_fraction = (p * multiplier - 1) / (multiplier - 1)
        else:
            # Traditional odds calculation
            # Convert American odds to decimal
            if odds_or_multiplier > 0:
                decimal_odds = (odds_or_multiplier / 100) + 1
            else:
                decimal_odds = (100 / abs(odds_or_multiplier)) + 1
            
            # Kelly formula: f = (bp - q) / b
            # where: b = odds-1, p = win probability, q = loss probability
            b = decimal_odds - 1
            p = win_probability
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b
        
        # Apply fractional Kelly for safety
        kelly_fraction *= self.kelly_multiplier
        
        # Ensure positive and within max limits
        kelly_fraction = max(0, min(kelly_fraction, self.max_bet_percentage))
        
        return kelly_fraction
    
    def adjust_for_bankroll_state(self, base_bet_size):
        """Adjust bet size based on current bankroll performance"""
        
        # Calculate current performance
        performance_ratio = self.current_bankroll / self.initial_bankroll
        
        # Reduce bet sizes if losing
        if performance_ratio < (1 - self.stop_loss_trigger):
            adjustment = 0.5  # Cut bet sizes in half
            print(f" LOSS PROTECTION: Reducing bet sizes by 50%")
        elif performance_ratio < 0.95:
            adjustment = 0.75  # Slight reduction
            print(f"WARNING: CAUTION MODE: Reducing bet sizes by 25%")
        elif performance_ratio > 1.20:
            adjustment = 1 + self.winning_streak_bonus  # Slight increase
            print(f"START: WINNING STREAK: Increasing bet sizes by 5%")
        else:
            adjustment = 1.0
        
        return base_bet_size * adjustment
    
    def check_daily_risk_limit(self, proposed_bet_amount):
        """Check if proposed bet exceeds daily risk limits"""
        
        daily_exposure = self.current_exposure + proposed_bet_amount
        daily_risk_percentage = daily_exposure / self.current_bankroll
        
        if daily_risk_percentage > self.max_daily_risk:
            max_allowed = (self.max_daily_risk * self.current_bankroll) - self.current_exposure
            return max(0, max_allowed)
        
        return proposed_bet_amount
    
    def calculate_recommended_bet(self, win_probability, odds_or_multiplier, confidence_level=1.0, is_fixed_multiplier=False, platform="traditional"):
        """Calculate the recommended bet amount for both traditional odds and fixed multipliers"""
        
        # Base Kelly calculation
        kelly_fraction = self.calculate_kelly_bet_size(win_probability, odds_or_multiplier, is_fixed_multiplier)
        
        # Adjust for confidence level
        kelly_fraction *= confidence_level
        
        # Additional adjustment for fixed multiplier platforms (more conservative)
        if is_fixed_multiplier:
            kelly_fraction *= 0.75  # 25% reduction for combo bet risk
        
        # Convert to dollar amount
        base_bet_amount = kelly_fraction * self.current_bankroll
        
        # Apply bankroll state adjustments
        adjusted_bet_amount = self.adjust_for_bankroll_state(base_bet_amount)
        
        # Check daily risk limits
        final_bet_amount = self.check_daily_risk_limit(adjusted_bet_amount)
        
        # Minimum bet check
        min_bet = 5  # $5 minimum
        if final_bet_amount < min_bet and final_bet_amount > 0:
            final_bet_amount = min_bet if self.current_bankroll >= min_bet else 0
        
        bet_type = f"{platform} {'Combo' if is_fixed_multiplier else 'Single'}"
        
        return {
            'recommended_amount': round(final_bet_amount, 2),
            'kelly_fraction': kelly_fraction,
            'confidence_adjusted': kelly_fraction * confidence_level,
            'risk_percentage': final_bet_amount / self.current_bankroll,
            'bet_type': bet_type,
            'reasoning': self.get_bet_reasoning(kelly_fraction, confidence_level, final_bet_amount, is_fixed_multiplier)
        }
    
    def get_bet_reasoning(self, kelly_fraction, confidence_level, final_amount, is_fixed_multiplier=False):
        """Provide reasoning for bet size recommendation"""
        
        bet_type = "COMBO" if is_fixed_multiplier else "SINGLE"
        
        if final_amount == 0:
            return f"ERROR: NO {bet_type} BET - Insufficient edge or bankroll protection"
        elif kelly_fraction < 0.01:
            return f" TINY {bet_type} BET - Very small edge detected"
        elif kelly_fraction < 0.05:
            return f"MONEY: SMALL {bet_type} BET - Modest edge with good value"
        elif kelly_fraction < 0.10:
            return f" SOLID {bet_type} BET - Strong edge and confidence"
        else:
            return f"START: LARGE {bet_type} BET - Exceptional edge (bet with caution)"
    
    def optimize_bet_portfolio(self, bet_opportunities):
        """Optimize allocation across multiple betting opportunities"""
        
        print("TARGET: OPTIMIZING BET PORTFOLIO")
        print("=" * 50)
        
        total_recommended = 0
        optimized_bets = []
        
        # Sort by expected value
        sorted_bets = sorted(bet_opportunities, key=lambda x: x.get('expected_value', 0), reverse=True)
        
        for bet in sorted_bets:
            # Calculate individual bet recommendation
            bet_rec = self.calculate_recommended_bet(
                bet['win_probability'],
                bet['odds'],
                bet.get('confidence', 1.0)
            )
            
            # Check if we have room for this bet
            if total_recommended + bet_rec['recommended_amount'] <= self.max_daily_risk * self.current_bankroll:
                optimized_bets.append({
                    **bet,
                    'recommended_amount': bet_rec['recommended_amount'],
                    'kelly_fraction': bet_rec['kelly_fraction'],
                    'reasoning': bet_rec['reasoning']
                })
                total_recommended += bet_rec['recommended_amount']
            else:
                # Partial allocation if possible
                remaining_budget = (self.max_daily_risk * self.current_bankroll) - total_recommended
                if remaining_budget >= 5:  # Minimum bet
                    optimized_bets.append({
                        **bet,
                        'recommended_amount': remaining_budget,
                        'kelly_fraction': remaining_budget / self.current_bankroll,
                        'reasoning': " PARTIAL - Limited by daily risk budget"
                    })
                    total_recommended += remaining_budget
                break
        
        # Portfolio summary
        portfolio_risk = total_recommended / self.current_bankroll
        expected_portfolio_value = sum([
            bet['recommended_amount'] * bet.get('expected_value', 0) / 100
            for bet in optimized_bets
        ])
        
        print(f"DATA: Portfolio Summary:")
        print(f"   MONEY: Total Allocation: ${total_recommended:.2f}")
        print(f"   PROGRESS: Portfolio Risk: {portfolio_risk:.1%}")
        print(f"   TARGET: Expected Value: ${expected_portfolio_value:.2f}")
        print(f"    Number of Bets: {len(optimized_bets)}")
        
        return optimized_bets
    
    def record_bet_result(self, bet_amount, won, odds, bet_type="single"):
        """Record the result of a bet"""
        
        if won:
            if odds > 0:
                payout = bet_amount * (odds / 100)
            else:
                payout = bet_amount * (100 / abs(odds))
            
            self.current_bankroll += payout
            result = "WIN"
        else:
            self.current_bankroll -= bet_amount
            payout = -bet_amount
            result = "LOSS"
        
        # Record in history
        bet_record = {
            'date': datetime.now(),
            'amount': bet_amount,
            'odds': odds,
            'result': result,
            'payout': payout,
            'bankroll_after': self.current_bankroll,
            'type': bet_type
        }
        
        self.bet_history.append(bet_record)
        
        # Update daily exposure
        self.current_exposure = max(0, self.current_exposure - bet_amount)
        
        print(f"PROGRESS: Bet Result: {result} | Amount: ${bet_amount} | Payout: ${payout:.2f}")
        print(f"MONEY: Current Bankroll: ${self.current_bankroll:.2f}")
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        
        if not self.bet_history:
            return {}
        
        df = pd.DataFrame(self.bet_history)
        
        total_bets = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        total_wagered = df['amount'].sum()
        total_profit = df['payout'].sum()
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
        
        # Winning/losing streaks
        current_streak = self.calculate_current_streak()
        
        # Sharpe-like ratio for betting
        returns = df['payout'] / df['amount']
        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
        
        return {
            'total_bets': total_bets,
            'win_rate': win_rate,
            'total_wagered': total_wagered,
            'total_profit': total_profit,
            'roi': roi,
            'current_bankroll': self.current_bankroll,
            'bankroll_change': (self.current_bankroll / self.initial_bankroll - 1) * 100,
            'current_streak': current_streak,
            'sharpe_ratio': sharpe_ratio
        }
    
    def calculate_current_streak(self):
        """Calculate current winning/losing streak"""
        
        if not self.bet_history:
            return {'type': 'none', 'length': 0}
        
        # Get recent results
        recent_results = [bet['result'] for bet in self.bet_history[-10:]]
        
        if not recent_results:
            return {'type': 'none', 'length': 0}
        
        current_result = recent_results[-1]
        streak_length = 1
        
        for i in range(len(recent_results) - 2, -1, -1):
            if recent_results[i] == current_result:
                streak_length += 1
            else:
                break
        
        return {
            'type': current_result.lower(),
            'length': streak_length
        }
    
    def generate_bankroll_report(self):
        """Generate comprehensive bankroll report"""
        
        print("MONEY: BANKROLL MANAGEMENT REPORT")
        print("=" * 50)
        
        metrics = self.get_performance_metrics()
        
        print(f"DATA: Performance Metrics:")
        print(f"   MONEY: Current Bankroll: ${metrics.get('current_bankroll', 0):.2f}")
        print(f"   PROGRESS: Bankroll Change: {metrics.get('bankroll_change', 0):+.1f}%")
        print(f"   TARGET: Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"    ROI: {metrics.get('roi', 0):+.1f}%")
        print(f"   DATA: Total Bets: {metrics.get('total_bets', 0)}")
        print(f"    Total Wagered: ${metrics.get('total_wagered', 0):.2f}")
        print(f"   LINEUP: Total Profit: ${metrics.get('total_profit', 0):+.2f}")
        
        streak = metrics.get('current_streak', {'type': 'none', 'length': 0})
        if streak['length'] > 0:
            emoji = "" if streak['type'] == 'win' else ""
            print(f"   {emoji} Current Streak: {streak['length']} {streak['type']}s")
        
        print(f"\n Risk Management:")
        print(f"   DATA: Current Exposure: ${self.current_exposure:.2f}")
        print(f"   TARGET: Daily Risk Limit: {self.max_daily_risk:.1%}")
        print(f"    Kelly Multiplier: {self.kelly_multiplier:.1%}")
        print(f"    Max Bet Size: {self.max_bet_percentage:.1%}")

def main():
    # Example usage
    bankroll = BankrollManager(initial_bankroll=1000)
    
    # Sample betting opportunities
    opportunities = [
        {
            'player': 'Aaron Judge',
            'prop': 'Over 1.5 Total Bases',
            'win_probability': 0.65,
            'odds': -110,
            'expected_value': 8.2,
            'confidence': 0.85
        },
        {
            'player': 'Shohei Ohtani',
            'prop': 'Over 0.5 Home Runs',
            'win_probability': 0.55,
            'odds': +150,
            'expected_value': 12.5,
            'confidence': 0.70
        }
    ]
    
    # Optimize portfolio
    optimized_bets = bankroll.optimize_bet_portfolio(opportunities)
    
    # Generate report
    bankroll.generate_bankroll_report()

if __name__ == "__main__":
    main()

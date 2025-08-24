"""
Backtest the automated betting system against historical results
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from automated_betting_system import AutomatedBettingSystem
import logging

def run_backtest(start_date, end_date, min_edge=0.05):
    """
    Backtest the betting system against historical data
    """
    system = AutomatedBettingSystem()
    
    # Load models
    if not system.load_all_models():
        print("ERROR: Failed to load models")
        return
    
    print(f" Running backtest from {start_date} to {end_date}")
    
    # Track results
    backtest_results = []
    total_bets = 0
    total_profit = 0
    
    # Simulate daily runs
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f" Testing {date_str}")
        
        try:
            # Generate predictions
            predictions = system.generate_all_predictions(date_str)
            
            if predictions:
                # Load sportsbook lines (you'd need historical data here)
                lines = system.load_sportsbook_lines()
                
                if lines:
                    # Find opportunities
                    opportunities = system.find_betting_opportunities(predictions, lines, min_edge)
                    
                    # Simulate betting results (you'd need actual game results)
                    daily_results = simulate_betting_results(opportunities, date_str)
                    backtest_results.extend(daily_results)
                    
                    print(f"  DATA: {len(opportunities)} opportunities found")
                
        except Exception as e:
            print(f"  ERROR: Error on {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    # Generate backtest report
    if backtest_results:
        df = pd.DataFrame(backtest_results)
        print(f"\nLINEUP: BACKTEST RESULTS:")
        print(f"Total Bets: {len(df)}")
        print(f"Win Rate: {df['won'].mean():.1%}")
        print(f"Total Profit: ${df['profit'].sum():.2f}")
        print(f"ROI: {df['profit'].sum() / len(df):.1%}")
        
        # Save results
        df.to_csv(f"backtest_results_{start_date}_{end_date}.csv", index=False)
        print(f"SUCCESS: Results saved to backtest_results_{start_date}_{end_date}.csv")

def simulate_betting_results(opportunities, date_str):
    """
    Simulate betting results (placeholder - you'd need actual game data)
    """
    results = []
    for opp in opportunities[:10]:  # Test top 10 opportunities
        # Simulate outcome based on model probability
        model_prob = opp['model_prob_over'] if opp['recommended_bet'] == 'OVER' else (1 - opp['model_prob_over'])
        won = np.random.random() < model_prob
        
        # Calculate profit/loss
        bet_amount = 100  # $100 per bet
        if won:
            profit = opp['expected_value'] * bet_amount
        else:
            profit = -bet_amount
        
        results.append({
            'date': date_str,
            'player': opp['player'],
            'category': opp['category'],
            'bet': opp['recommended_bet'],
            'line': opp['line'],
            'prediction': opp['prediction'],
            'edge': opp['edge'],
            'won': won,
            'profit': profit
        })
    
    return results

if __name__ == "__main__":
    # Run backtest for last week
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    run_backtest(start_date, end_date, min_edge=0.10)

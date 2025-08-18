#!/usr/bin/env python3
"""
prop_backtest_validator.py
Validates prop predictions against actual results with detailed analysis
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_latest_prop_opportunities():
    """Load latest prop betting opportunities"""
    betting_dir = "../data"
    files = [f for f in os.listdir(betting_dir) if f.startswith('betting_opportunities_') and f.endswith('.csv')]
    
    if not files:
        print("ERROR: No prop opportunities files found")
        return None
    
    latest_file = max(files)
    file_path = os.path.join(betting_dir, latest_file)
    
    try:
        df = pd.read_csv(file_path)
        print(f"SUCCESS: Loaded prop opportunities: {latest_file}")
        return df
    except Exception as e:
        print(f"ERROR: Error loading prop opportunities: {e}")
        return None

def load_actual_results():
    """Load actual results for validation"""
    results_dir = "../data"
    
    # Try latest results first
    latest_file = os.path.join(results_dir, "actual_results_latest.csv")
    if os.path.exists(latest_file):
        try:
            df = pd.read_csv(latest_file)
            print(f"SUCCESS: Loaded actual results: {len(df)} players")
            return df
        except Exception as e:
            print(f"ERROR: Error loading latest results: {e}")
    
    # Try yesterday's results
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_file = os.path.join(results_dir, f"actual_results_{yesterday.strftime('%Y%m%d')}.csv")
    if os.path.exists(yesterday_file):
        try:
            df = pd.read_csv(yesterday_file)
            print(f"SUCCESS: Loaded yesterday's results: {len(df)} players")
            return df
        except Exception as e:
            print(f"ERROR: Error loading yesterday's results: {e}")
    
    print("ERROR: No actual results found for validation")
    return None

def validate_prop_predictions(prop_df, results_df):
    """Validate prop predictions against actual results"""
    if prop_df is None or results_df is None:
        return None
    
    validation_results = []
    
    # Clean results data
    if 'name' in results_df.columns:
        results_df['clean_name'] = results_df['name'].str.strip().str.title()
    
    print(f"\n Validating {len(prop_df)} prop predictions...")
    
    for idx, prop in prop_df.iterrows():
        player_name = prop.get('player', '').strip().title()
        prop_type = prop.get('prop_type', '')
        prediction = prop.get('prediction', 0)
        line = prop.get('line', 0)
        bet_recommendation = prop.get('bet', '')
        edge = prop.get('edge', 0)
        
        # Find matching player in results
        if 'clean_name' in results_df.columns:
            player_results = results_df[results_df['clean_name'].str.contains(player_name.split()[0], na=False, case=False)]
        else:
            player_results = results_df[results_df['name'].str.contains(player_name.split()[0], na=False, case=False)]
        
        if len(player_results) == 0:
            continue
        
        player_result = player_results.iloc[0]
        
        # Get actual performance based on prop type
        actual_value = None
        if 'total_bases' in prop_type.lower():
            actual_value = player_result.get('total_bases', 0)
        elif 'hits' in prop_type.lower():
            actual_value = player_result.get('hits', 0)
        elif 'runs' in prop_type.lower():
            actual_value = player_result.get('runs', 0)
        elif 'rbi' in prop_type.lower():
            actual_value = player_result.get('rbis', 0)
        elif 'home_runs' in prop_type.lower():
            actual_value = player_result.get('home_runs', 0)
        elif 'strikeouts' in prop_type.lower():
            actual_value = player_result.get('strikeouts', 0)
        elif 'stolen_bases' in prop_type.lower():
            actual_value = player_result.get('stolen_bases', 0)
        
        if actual_value is not None:
            # Determine if bet was correct
            bet_correct = False
            if bet_recommendation.upper() == 'OVER' and actual_value > line:
                bet_correct = True
            elif bet_recommendation.upper() == 'UNDER' and actual_value < line:
                bet_correct = True
            
            validation_results.append({
                'player': player_name,
                'prop_type': prop_type,
                'line': line,
                'prediction': prediction,
                'actual': actual_value,
                'bet': bet_recommendation,
                'bet_correct': bet_correct,
                'edge': edge,
                'fanduel_points': player_result.get('fanduel_points', 0),
                'team': player_result.get('team', ''),
                'date': player_result.get('date', '')
            })
    
    return pd.DataFrame(validation_results)

def generate_prop_validation_report(validation_df):
    """Generate comprehensive prop validation report"""
    if validation_df is None or len(validation_df) == 0:
        print("ERROR: No validation data available")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"../data/prop_validation_report_{timestamp}.txt"
    csv_file = f"../data/prop_validation_details_{timestamp}.csv"
    
    # Save detailed CSV
    validation_df.to_csv(csv_file, index=False)
    
    # Calculate summary statistics
    total_bets = len(validation_df)
    correct_bets = validation_df['bet_correct'].sum()
    accuracy = (correct_bets / total_bets * 100) if total_bets > 0 else 0
    
    avg_edge = validation_df['edge'].mean()
    total_fantasy_points = validation_df['fanduel_points'].sum()
    avg_fantasy_points = validation_df['fanduel_points'].mean()
    
    # Generate report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("TARGET: PROP BETTING VALIDATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("DATA: OVERALL PERFORMANCE:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Prop Bets Validated: {total_bets}\n")
        f.write(f"Correct Predictions: {correct_bets}\n")
        f.write(f"Accuracy Rate: {accuracy:.1f}%\n")
        f.write(f"Average Edge: {avg_edge:.1f}%\n")
        f.write(f"Total Fantasy Points: {total_fantasy_points:.1f}\n")
        f.write(f"Average Fantasy Points per Player: {avg_fantasy_points:.1f}\n\n")
        
        f.write("TARGET: TOP 10 SUCCESSFUL PREDICTIONS:\n")
        f.write("-" * 40 + "\n")
        correct_predictions = validation_df[validation_df['bet_correct']].sort_values('edge', ascending=False).head(10)
        for idx, row in correct_predictions.iterrows():
            f.write(f"{row['player']} {row['prop_type']} {row['bet']} {row['line']}\n")
            f.write(f"  Predicted: {row['prediction']:.1f} | Actual: {row['actual']:.1f} | Edge: {row['edge']:.1f}% | FP: {row['fanduel_points']:.1f}\n\n")
        
        f.write("ERROR: TOP 5 FAILED PREDICTIONS:\n")
        f.write("-" * 40 + "\n")
        failed_predictions = validation_df[~validation_df['bet_correct']].sort_values('edge', ascending=False).head(5)
        for idx, row in failed_predictions.iterrows():
            f.write(f"{row['player']} {row['prop_type']} {row['bet']} {row['line']}\n")
            f.write(f"  Predicted: {row['prediction']:.1f} | Actual: {row['actual']:.1f} | Edge: {row['edge']:.1f}% | FP: {row['fanduel_points']:.1f}\n\n")
        
        f.write("PROGRESS: PROP TYPE BREAKDOWN:\n")
        f.write("-" * 40 + "\n")
        prop_type_stats = validation_df.groupby('prop_type').agg({
            'bet_correct': ['count', 'sum', 'mean'],
            'edge': 'mean',
            'fanduel_points': 'mean'
        }).round(2)
        
        for prop_type in prop_type_stats.index:
            count = prop_type_stats.loc[prop_type, ('bet_correct', 'count')]
            correct = prop_type_stats.loc[prop_type, ('bet_correct', 'sum')]
            accuracy = prop_type_stats.loc[prop_type, ('bet_correct', 'mean')] * 100
            avg_edge = prop_type_stats.loc[prop_type, ('edge', 'mean')]
            avg_fp = prop_type_stats.loc[prop_type, ('fanduel_points', 'mean')]
            f.write(f"{prop_type}: {correct}/{count} ({accuracy:.1f}%) | Avg Edge: {avg_edge:.1f}% | Avg FP: {avg_fp:.1f}\n")
    
    print(f"SUCCESS: Prop validation report saved: {report_file}")
    print(f"SUCCESS: Detailed validation CSV saved: {csv_file}")
    print(f"\nDATA: QUICK SUMMARY:")
    print(f"   TARGET: Accuracy: {accuracy:.1f}% ({correct_bets}/{total_bets} correct)")
    print(f"   MONEY: Average Edge: {avg_edge:.1f}%")
    print(f"   PROGRESS: Total Fantasy Points: {total_fantasy_points:.1f}")

def main():
    print(" PROP BETTING VALIDATION ANALYSIS")
    print("=" * 50)
    
    # Load data
    prop_df = load_latest_prop_opportunities()
    results_df = load_actual_results()
    
    # Validate predictions
    validation_df = validate_prop_predictions(prop_df, results_df)
    
    # Generate report
    generate_prop_validation_report(validation_df)

if __name__ == "__main__":
    main()

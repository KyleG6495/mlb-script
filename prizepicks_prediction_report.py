#!/usr/bin/env python3
"""
PrizePicks ML Model Predictions Report

Shows clear breakdown of what our ML models are predicting vs PrizePicks lines
"""

import pandas as pd
import numpy as np
from datetime import datetime

def create_prediction_report():
    """Create a detailed report showing our ML predictions vs PrizePicks lines"""
    
    # Create output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    txt_output_file = f"../data/prizepicks_prediction_report_{timestamp}.txt"
    csv_output_file = f"../data/prizepicks_prediction_report_{timestamp}.csv"
    
    # Function to print to both console and file
    def dual_print(text, file_handle=None):
        print(text)
        if file_handle:
            file_handle.write(text + "\n")
    
    # Load the EV analysis results
    ev_file = '../data/prizepicks_ev_analysis_enhanced_20250721_1655.csv'
    try:
        df = pd.read_csv(ev_file)
        print(f"DATA: Loaded {len(df)} betting opportunities")
    except Exception as e:
        print(f"ERROR: Error loading EV results: {e}")
        return
    
    # Create enhanced CSV with additional analysis columns
    enhanced_df = df.copy()
    
    # Add confidence level based on prediction vs line comparison
    def get_confidence(row):
        if row['bet_type'] == 'OVER':
            return 'HIGH' if row['prediction'] > row['line'] * 1.2 else 'MEDIUM'
        else:  # UNDER
            return 'HIGH' if row['prediction'] < row['line'] * 0.8 else 'MEDIUM'
    
    enhanced_df['confidence'] = enhanced_df.apply(get_confidence, axis=1)
    
    # Add model vs market percentage
    enhanced_df['model_vs_market_pct'] = ((enhanced_df['prediction'] / enhanced_df['line']) - 1) * 100
    
    # Add recommendation strength
    def get_strength(edge):
        if edge >= 0.8:
            return 'VERY_STRONG'
        elif edge >= 0.6:
            return 'STRONG'
        elif edge >= 0.3:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    enhanced_df['recommendation_strength'] = enhanced_df['edge'].apply(get_strength)
    
    # Save the enhanced CSV
    enhanced_df.to_csv(csv_output_file, index=False)
    print(f" Enhanced CSV report saved to: {csv_output_file}")
    
    # Create summary statistics CSV
    summary_csv_file = f"../data/prizepicks_summary_stats_{timestamp}.csv"
    
    # Stat type breakdown
    stat_summary = df.groupby('stat').agg({
        'prediction': ['mean', 'min', 'max', 'std'],
        'line': ['mean', 'min', 'max'],
        'edge': ['mean', 'max'],
        'prob_win': 'mean'
    }).round(3)
    
    # Flatten column names
    stat_summary.columns = ['_'.join(col).strip() for col in stat_summary.columns]
    stat_summary['stat_type'] = stat_summary.index
    
    # Add bet type counts
    bet_counts = df.groupby(['stat', 'bet_type']).size().unstack(fill_value=0)
    stat_summary = stat_summary.merge(bet_counts, left_index=True, right_index=True, how='left')
    
    # Reset index and save
    stat_summary.reset_index(drop=True, inplace=True)
    stat_summary.to_csv(summary_csv_file, index=False)
    print(f" Summary statistics CSV saved to: {summary_csv_file}")
    
    # Also create the text report
    with open(txt_output_file, 'w', encoding='utf-8') as f:
    
        # Group by stat type to show model performance by category
        stat_types = df['stat'].unique()
        
        for stat in sorted(stat_types):
            stat_df = df[df['stat'] == stat].copy()
            if len(stat_df) == 0:
                continue
                
            dual_print(f"\nTARGET: {stat.upper()} PREDICTIONS", f)
            dual_print("-" * 50, f)
            
            # Show top predictions for this stat
            top_predictions = stat_df.sort_values('edge', ascending=False).head(15)
            
            for i, row in enumerate(top_predictions.itertuples(), 1):
                line = row.line
                prediction = row.prediction
                bet_type = row.bet_type
                edge = row.edge
                
                # Format the prediction comparison
                if bet_type == "OVER":
                    comparison = f"Model: {prediction:.3f} vs Line: {line}  Bet OVER"
                    confidence = " HIGH" if prediction > line * 1.2 else "WARNING: MEDIUM"
                else:
                    comparison = f"Model: {prediction:.3f} vs Line: {line}  Bet UNDER"
                    confidence = " HIGH" if prediction < line * 0.8 else "WARNING: MEDIUM"
                
                dual_print(f"{i:2d}. {row.player:<20} | {comparison}", f)
                dual_print(f"    Edge: {edge:+.1%} | Confidence: {confidence}", f)
            
            # Summary stats for this category
            avg_prediction = stat_df['prediction'].mean()
            avg_line = stat_df['line'].mean()
            over_count = len(stat_df[stat_df['bet_type'] == 'OVER'])
            under_count = len(stat_df[stat_df['bet_type'] == 'UNDER'])
            
            dual_print(f"\nPROGRESS: {stat} SUMMARY:", f)
            dual_print(f"   Avg Model Prediction: {avg_prediction:.3f}", f)
            dual_print(f"   Avg PrizePicks Line:  {avg_line:.3f}", f)
            dual_print(f"   Model vs Market:      {((avg_prediction/avg_line - 1) * 100):+.1f}%", f)
            dual_print(f"   OVER bets: {over_count} | UNDER bets: {under_count}", f)
    
        # Overall model insights
        dual_print(f"\n OVERALL MODEL INSIGHTS", f)
        dual_print("=" * 50, f)
        
        # Show which players our models are most confident about
        player_opportunities = df.groupby('player').agg({
            'edge': ['mean', 'count'],
            'prediction': 'mean'
        }).round(3)
        
        player_opportunities.columns = ['avg_edge', 'num_bets', 'avg_prediction']
        player_opportunities = player_opportunities.sort_values('avg_edge', ascending=False)
        
        dual_print("TARGET: TOP PLAYERS BY MODEL CONFIDENCE:", f)
        top_players = player_opportunities.head(10)
        for player, stats in top_players.iterrows():
            dual_print(f"   {player:<25} | {stats['num_bets']} bets | {stats['avg_edge']:+.1%} avg edge", f)
        
        # Show stat type breakdown
        dual_print(f"\nDATA: STAT TYPE BREAKDOWN:", f)
        stat_summary = df.groupby('stat').agg({
            'prediction': ['mean', 'min', 'max'],
            'line': ['mean', 'min', 'max'],
            'edge': 'mean'
        }).round(3)
        
        for stat in stat_summary.index:
            pred_avg = stat_summary.loc[stat, ('prediction', 'mean')]
            pred_range = f"{stat_summary.loc[stat, ('prediction', 'min')]}-{stat_summary.loc[stat, ('prediction', 'max')]}"
            line_avg = stat_summary.loc[stat, ('line', 'mean')]
            avg_edge = stat_summary.loc[stat, ('edge', 'mean')]
            
            dual_print(f"   {stat:<20} | Model Avg: {pred_avg:.3f} ({pred_range}) | Line Avg: {line_avg:.3f} | Edge: {avg_edge:+.1%}", f)
        
        dual_print(f"\nSUCCESS: Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f)
        dual_print(f" Text report saved to: {txt_output_file}", f)
    
    print(f"\nDATA: REPORT FILES GENERATED:")
    print(f"   Enhanced CSV: {csv_output_file}")
    print(f"   Summary Stats: {summary_csv_file}")
    print(f"   Text Report: {txt_output_file}")

if __name__ == "__main__":
    create_prediction_report()

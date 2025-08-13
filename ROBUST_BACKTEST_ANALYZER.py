#!/usr/bin/env python3
"""
ROBUST BACKTEST ANALYZER
Fixes the player matching issues in the backtest system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
import difflib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_name(name):
    """Normalize player names for better matching"""
    if pd.isna(name):
        return ""
    
    # Remove special characters and normalize spacing
    name = str(name).strip()
    name = name.replace("'", "").replace(".", "").replace("-", " ")
    name = " ".join(name.split())  # Remove extra spaces
    
    # Handle common name variations
    name_map = {
        'Freddie Freeman': 'Frederick Freeman',
        'Mookie Betts': 'Markus Betts',
        'Ronald Acuña Jr.': 'Ronald Acuna Jr',
        'Vladimir Guerrero Jr.': 'Vladimir Guerrero Jr',
        'Fernando Tatis Jr.': 'Fernando Tatis Jr',
        'Bo Bichette': 'Bo Bichette',
        'Xander Bogaerts': 'Xander Bogaerts'
    }
    
    return name_map.get(name, name)

def fuzzy_match_player(lineup_name, actual_players, threshold=0.8):
    """Use difflib matching to find the best player match"""
    normalized_lineup = normalize_name(lineup_name)
    
    # Try exact match first
    for _, player in actual_players.iterrows():
        if normalize_name(player['name']) == normalized_lineup:
            return player
    
    # Try difflib matching
    actual_names = [normalize_name(name) for name in actual_players['name']]
    best_matches = difflib.get_close_matches(normalized_lineup, actual_names, n=1, cutoff=threshold)
    
    if best_matches:
        matched_name = best_matches[0]
        matched_idx = actual_names.index(matched_name)
        return actual_players.iloc[matched_idx]
    
    # Try last name matching as fallback
    lineup_last = normalized_lineup.split()[-1] if normalized_lineup else ""
    if len(lineup_last) > 2:  # Avoid matching single letters
        for _, player in actual_players.iterrows():
            actual_last = normalize_name(player['name']).split()[-1] if normalize_name(player['name']) else ""
            if lineup_last.lower() == actual_last.lower():
                return player
    
    return None

def find_most_recent_lineup_file(data_dir):
    """Find the most recent enhanced ML DFS lineup file from yesterday"""
    from datetime import datetime, timedelta
    import glob
    
    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    
    # Look for lineup files from yesterday
    pattern = os.path.join(data_dir, f"enhanced_ml_dfs_lineups_{yesterday_str}_*.csv")
    lineup_files = glob.glob(pattern)
    
    if lineup_files:
        # Return the most recent file from yesterday
        latest_file = max(lineup_files, key=os.path.getmtime)
        logger.info(f"📁 Found yesterday's lineup file: {os.path.basename(latest_file)}")
        return latest_file
    
    # If no yesterday files, look for most recent file
    pattern = os.path.join(data_dir, "enhanced_ml_dfs_lineups_*.csv")
    all_lineup_files = glob.glob(pattern)
    
    if all_lineup_files:
        latest_file = max(all_lineup_files, key=os.path.getmtime)
        logger.info(f"📁 Using most recent lineup file: {os.path.basename(latest_file)}")
        return latest_file
    
    return None

def find_most_recent_actual_results(data_dir):
    """Find the most recent actual results file from yesterday"""
    from datetime import datetime, timedelta
    import glob
    
    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    
    # Look for actual results from yesterday
    yesterday_file = os.path.join(data_dir, f"actual_results_{yesterday_str}.csv")
    if os.path.exists(yesterday_file):
        logger.info(f"📁 Found yesterday's actual results: actual_results_{yesterday_str}.csv")
        return yesterday_file
    
    # If no yesterday results, use latest available
    latest_file = os.path.join(data_dir, "actual_results_latest.csv")
    if os.path.exists(latest_file):
        logger.info(f"📁 Using latest actual results: actual_results_latest.csv")
        return latest_file
    
    # Look for most recent actual results file
    pattern = os.path.join(data_dir, "actual_results_*.csv")
    results_files = glob.glob(pattern)
    results_files = [f for f in results_files if 'latest' not in f]  # Exclude latest.csv
    
    if results_files:
        latest_file = max(results_files, key=os.path.getmtime)
        logger.info(f"📁 Using most recent actual results: {os.path.basename(latest_file)}")
        return latest_file
    
    return None

def analyze_lineup_performance(lineup_file, actual_results_file, output_dir):
    """Analyze lineup performance with robust player matching"""
    
    logger.info(f"🔍 ANALYZING LINEUP PERFORMANCE")
    logger.info(f"📂 Lineup file: {lineup_file}")
    logger.info(f"📂 Actual results: {actual_results_file}")
    
    # Load data
    try:
        lineup_df = pd.read_csv(lineup_file)
        actual_df = pd.read_csv(actual_results_file)
        
        logger.info(f"📊 Loaded {len(lineup_df)} lineup entries")
        logger.info(f"📊 Loaded {len(actual_df)} actual results")
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        return None
    
    # Get unique lineups
    unique_lineups = lineup_df['lineup_id'].unique()
    logger.info(f"📊 Found {len(unique_lineups)} unique lineups")
    
    results = []
    detailed_results = []
    
    for lineup_id in unique_lineups:
        lineup_players = lineup_df[lineup_df['lineup_id'] == lineup_id].copy()
        
        total_projected = 0
        total_actual = 0
        total_salary = 0
        players_found = 0
        total_players = len(lineup_players)
        
        lineup_details = []
        
        for _, player in lineup_players.iterrows():
            player_name = player['name']
            projected_fppg = player.get('ml_projected_fppg', 0)
            salary = player.get('salary', 0)
            position = player.get('position', 'Unknown')
            
            total_projected += projected_fppg
            total_salary += salary
            
            # Find matching player in actual results
            matched_player = fuzzy_match_player(player_name, actual_df)
            
            if matched_player is not None:
                actual_fppg = matched_player['fanduel_points']
                players_found += 1
                match_status = "✅ FOUND"
                actual_name = matched_player['name']
            else:
                actual_fppg = 0
                match_status = "❌ NOT FOUND"
                actual_name = "N/A"
            
            total_actual += actual_fppg
            
            player_detail = {
                'lineup_id': lineup_id,
                'slot': player.get('slot', 0),
                'player_name': player_name,
                'actual_name': actual_name,
                'position': position,
                'salary': salary,
                'projected_fppg': projected_fppg,
                'actual_fppg': actual_fppg,
                'difference': actual_fppg - projected_fppg,
                'match_status': match_status
            }
            
            lineup_details.append(player_detail)
            detailed_results.append(player_detail)
        
        # Calculate lineup metrics
        accuracy_rate = (players_found / total_players) * 100 if total_players > 0 else 0
        projection_accuracy = (total_actual / total_projected) * 100 if total_projected > 0 else 0
        
        lineup_result = {
            'lineup_id': lineup_id,
            'total_players': total_players,
            'players_found': players_found,
            'accuracy_rate': accuracy_rate,
            'total_salary': total_salary,
            'projected_fppg': total_projected,
            'actual_fppg': total_actual,
            'difference': total_actual - total_projected,
            'projection_accuracy': projection_accuracy,
            'contest_type': lineup_players.iloc[0].get('contest_type', 'Unknown'),
            'strategy': lineup_players.iloc[0].get('strategy_description', 'Unknown')
        }
        
        results.append(lineup_result)
        
        logger.info(f"📊 Lineup {lineup_id}: {players_found}/{total_players} players found ({accuracy_rate:.1f}%)")
        logger.info(f"💰 Projected: {total_projected:.1f} | Actual: {total_actual:.1f} | Diff: {total_actual - total_projected:+.1f}")
    
    # Create summary DataFrames
    summary_df = pd.DataFrame(results)
    details_df = pd.DataFrame(detailed_results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    summary_file = os.path.join(output_dir, f'robust_backtest_summary_{timestamp}.csv')
    details_file = os.path.join(output_dir, f'robust_backtest_details_{timestamp}.csv')
    
    summary_df.to_csv(summary_file, index=False)
    details_df.to_csv(details_file, index=False)
    
    # Generate summary statistics
    overall_stats = {
        'total_lineups': len(summary_df),
        'avg_players_found': summary_df['players_found'].mean(),
        'avg_accuracy_rate': summary_df['accuracy_rate'].mean(),
        'avg_projected_fppg': summary_df['projected_fppg'].mean(),
        'avg_actual_fppg': summary_df['actual_fppg'].mean(),
        'avg_difference': summary_df['difference'].mean(),
        'avg_projection_accuracy': summary_df['projection_accuracy'].mean(),
        'best_lineup_id': summary_df.loc[summary_df['actual_fppg'].idxmax(), 'lineup_id'],
        'best_lineup_score': summary_df['actual_fppg'].max(),
        'worst_lineup_id': summary_df.loc[summary_df['actual_fppg'].idxmin(), 'lineup_id'],
        'worst_lineup_score': summary_df['actual_fppg'].min()
    }
    
    # Print summary
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 ROBUST BACKTEST SUMMARY")
    logger.info(f"="*60)
    logger.info(f"📋 Total Lineups Analyzed: {overall_stats['total_lineups']}")
    logger.info(f"🎯 Average Players Found: {overall_stats['avg_players_found']:.1f}/9 ({overall_stats['avg_accuracy_rate']:.1f}%)")
    logger.info(f"💰 Average Projected FPPG: {overall_stats['avg_projected_fppg']:.1f}")
    logger.info(f"💰 Average Actual FPPG: {overall_stats['avg_actual_fppg']:.1f}")
    logger.info(f"📈 Average Difference: {overall_stats['avg_difference']:+.1f}")
    logger.info(f"🎯 Projection Accuracy: {overall_stats['avg_projection_accuracy']:.1f}%")
    logger.info(f"🏆 Best Lineup: #{overall_stats['best_lineup_id']} ({overall_stats['best_lineup_score']:.1f} FPPG)")
    logger.info(f"💥 Worst Lineup: #{overall_stats['worst_lineup_id']} ({overall_stats['worst_lineup_score']:.1f} FPPG)")
    logger.info(f"="*60)
    
    # Show top/bottom performers
    if not details_df.empty:
        found_players = details_df[details_df['match_status'] == '✅ FOUND']
        if not found_players.empty:
            logger.info(f"\n🎯 TOP PERFORMERS:")
            top_performers = found_players.nlargest(5, 'actual_fppg')
            for _, player in top_performers.iterrows():
                logger.info(f"   • {player['player_name']}: {player['actual_fppg']:.1f} FPPG ({player['difference']:+.1f} vs proj)")
            
            logger.info(f"\n💥 BIGGEST DISAPPOINTMENTS:")
            disappointments = found_players.nsmallest(5, 'difference')
            for _, player in disappointments.iterrows():
                logger.info(f"   • {player['player_name']}: {player['actual_fppg']:.1f} FPPG ({player['difference']:+.1f} vs proj)")
    
    logger.info(f"\n💾 Results saved:")
    logger.info(f"   • Summary: {summary_file}")
    logger.info(f"   • Details: {details_file}")
    
    return summary_df, details_df

def main():
    """Main execution function with automatic date handling"""
    
    # File paths
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    
    logger.info(f"🔍 STARTING ROBUST BACKTEST ANALYSIS")
    logger.info(f"📅 Automatically finding yesterday's lineups and actual results")
    
    # Automatically find the most recent lineup and actual results files
    lineup_file = find_most_recent_lineup_file(data_dir)
    actual_results_file = find_most_recent_actual_results(data_dir)
    
    # Check if files exist
    if not lineup_file or not os.path.exists(lineup_file):
        logger.error(f"❌ No lineup file found. Expected enhanced_ml_dfs_lineups from yesterday.")
        logger.error(f"📋 Make sure you generated lineups yesterday using the enhanced ML system.")
        return
    
    if not actual_results_file or not os.path.exists(actual_results_file):
        logger.error(f"❌ No actual results file found.")
        logger.error(f"📋 Run collect_actual_results_enhanced.py to get yesterday's game results.")
        return
    
    logger.info(f"📂 Using lineup file: {os.path.basename(lineup_file)}")
    logger.info(f"📂 Using actual results: {os.path.basename(actual_results_file)}")
    
    # Run analysis
    summary_df, details_df = analyze_lineup_performance(lineup_file, actual_results_file, data_dir)
    
    logger.info(f"✅ ROBUST BACKTEST ANALYSIS COMPLETE!")
    logger.info(f"📊 Files saved in: {data_dir}")
    
    return summary_df, details_df

if __name__ == "__main__":
    main()

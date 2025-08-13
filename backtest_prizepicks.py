#!/usr/bin/env python3
"""
BACKTEST PRIZEPICKS PREDICTIONS
===============================
Analyzes PrizePicks prop bet predictions against actual results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import glob
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def find_latest_prizepicks_file():
    """Find the most recent PrizePicks analysis file"""
    # Try multiple file patterns in order of preference
    patterns = [
        str(BASE_DIR / "prizepicks_real_ev_*.csv"),
        str(BASE_DIR.parent / "Scripts" / "betting_analysis" / "betting_opportunities_*.csv"),
        str(BASE_DIR / "betting_opportunities_*.csv")
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            # Get most recent file
            latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
            logger.info(f"📁 Found PrizePicks data in: {Path(latest_file).name}")
            return latest_file
    
    logger.warning("⚠️ No PrizePicks files found")
    return None

def load_prizepicks_data(file_path):
    """Load PrizePicks data from betting opportunities file"""
    if not file_path:
        return None
    
    df = pd.read_csv(file_path)
    
    # Filter for PrizePicks entries only
    prizepicks_df = df[df['source'] == 'prizepicks'].copy()
    
    if len(prizepicks_df) == 0:
        logger.warning("⚠️ No PrizePicks entries found in file")
        return None
    
    # Convert to expected format for analysis
    prizepicks_df['Player'] = prizepicks_df['player']
    prizepicks_df['Stat'] = prizepicks_df['category'].str.replace('_', ' ').str.title()
    prizepicks_df['Line'] = prizepicks_df['line']
    prizepicks_df['Bet Type'] = prizepicks_df['recommended_bet']
    
    logger.info(f"📊 Loaded {len(prizepicks_df)} PrizePicks entries")
    return prizepicks_df

def load_actual_results():
    """Load actual game results"""
    actual_file = BASE_DIR / "actual_results_latest.csv"
    
    if not actual_file.exists():
        logger.warning("⚠️ No actual results file found")
        return None
    
    df = pd.read_csv(actual_file)
    logger.info(f"📊 Loaded actual results for {len(df)} players")
    return df

def map_prop_to_actual_stat(prop_type, actual_player):
    """Map PrizePicks prop type to actual stat value"""
    prop_mapping = {
        'Hits': actual_player.get('hits', 0),
        'Home Runs': actual_player.get('home_runs', 0),
        'RBIs': actual_player.get('rbis', 0),
        'Runs': actual_player.get('runs', 0),
        'Total Bases': actual_player.get('total_bases', 0),
        'Stolen Bases': actual_player.get('stolen_bases', 0),
        'Strikeouts': actual_player.get('strikeouts', 0),  # For pitchers
        'Pitcher Strikeouts': actual_player.get('strikeouts', 0),
        'Walks': actual_player.get('walks', 0),
        'Hits Allowed': actual_player.get('hits_allowed', 0),
        'Earned Runs': actual_player.get('earned_runs', 0),
        'Innings Pitched': actual_player.get('innings_pitched', 0)
    }
    
    return prop_mapping.get(prop_type, 0)

def analyze_prizepicks_performance(prizepicks_df, actual_df):
    """Analyze PrizePicks predictions vs actual results"""
    logger.info("💰 Analyzing PrizePicks performance...")
    
    if prizepicks_df is None or actual_df is None:
        logger.warning("⚠️ Missing data for PrizePicks analysis")
        return pd.DataFrame(), {}
    
    results = []
    
    for _, pick in prizepicks_df.iterrows():
        # Parse player name from different possible columns
        player_name = pick.get('Player', pick.get('player_name', ''))
        
        # Parse prop type from 'Stat' column
        prop_type = pick.get('Stat', pick.get('prop_type', ''))
        
        # Parse bet direction from 'Bet Type' column
        bet_type = pick.get('Bet Type', pick.get('pick_direction', 'OVER'))
        pick_direction = 'under' if 'UNDER' in bet_type.upper() else 'over'
        
        # Parse line value
        line_value = pick.get('Line', pick.get('pick_value', '0'))
        
        # Handle line values with U/O prefixes (like U1.5, O0.5)
        if isinstance(line_value, str):
            if line_value.startswith(('U', 'O')):
                pick_value = float(line_value[1:])  # Remove U/O prefix
            else:
                try:
                    pick_value = float(line_value)
                except (ValueError, TypeError):
                    pick_value = 0.0
        else:
            pick_value = float(line_value) if line_value else 0.0
        
        # Try different matching strategies for players
        actual_player = None
        for _, actual in actual_df.iterrows():
            if actual['name'].lower().strip() == player_name.lower().strip():
                actual_player = actual
                break
        
        if actual_player is None:
            # Try partial name matching
            for _, actual in actual_df.iterrows():
                player_parts = player_name.lower().split()
                actual_parts = actual['name'].lower().split()
                if len(player_parts) >= 2 and len(actual_parts) >= 2:
                    # Match first and last name
                    if (player_parts[0] in actual_parts and player_parts[-1] in actual_parts):
                        actual_player = actual
                        break
        
        if actual_player is not None:
            # Get actual stat value
            actual_value = map_prop_to_actual_stat(prop_type, actual_player.to_dict())
            
            # Determine if pick won
            if pick_direction == 'over':
                pick_won = actual_value > pick_value
            else:  # under
                pick_won = actual_value < pick_value
            
            # Get prediction data
            our_prob = pick.get('Our Probability', '50%')
            if isinstance(our_prob, str) and our_prob.endswith('%'):
                our_prob = float(our_prob.replace('%', '')) / 100
            else:
                our_prob = float(our_prob) if our_prob else 0.5
            
            # Parse edge percentage
            edge_str = pick.get('Edge %', '0%')
            if isinstance(edge_str, str) and edge_str.endswith('%'):
                edge = float(edge_str.replace('%', '')) / 100
            else:
                edge = float(edge_str) if edge_str else 0.0
            
            results.append({
                'player_name': player_name,
                'prop_type': prop_type,
                'pick_value': pick_value,
                'pick_direction': pick_direction,
                'actual_value': actual_value,
                'pick_won': pick_won,
                'our_probability': our_prob,
                'implied_probability': 0.5,  # Default if not available
                'edge': edge,
                'ev': pick.get('Expected Value', 0),
                'confidence': pick.get('Confidence', 'Medium')
            })
        else:
            # Player not found in actual results
            results.append({
                'player_name': player_name,
                'prop_type': prop_type,
                'pick_value': pick_value,
                'pick_direction': pick_direction,
                'actual_value': None,
                'pick_won': None,
                'our_probability': 0.5,
                'implied_probability': 0.5,
                'edge': 0.0,
                'ev': pick.get('ev', 0),
                'confidence': pick.get('confidence', 'Medium'),
                'note': 'Player not found in actual results'
            })
    
    results_df = pd.DataFrame(results)
    
    # Calculate summary statistics
    if len(results_df) > 0:
        won_picks = results_df['pick_won'].sum()
        total_picks = len(results_df[results_df['pick_won'].notna()])
        hit_rate = (won_picks / total_picks * 100) if total_picks > 0 else 0
        
        summary = {
            'total_picks': len(results_df),
            'picks_with_results': total_picks,
            'winning_picks': won_picks,
            'hit_rate_pct': hit_rate,
            'avg_edge': results_df['edge'].mean(),
            'avg_ev': results_df['ev'].mean(),
            'high_confidence_hits': len(results_df[(results_df['confidence'] == 'High') & (results_df['pick_won'] == True)]),
            'high_confidence_total': len(results_df[results_df['confidence'] == 'High'])
        }
    else:
        summary = {}
    
    return results_df, summary

def analyze_by_prop_type(results_df):
    """Analyze performance by prop type"""
    if len(results_df) == 0:
        return pd.DataFrame()
    
    prop_analysis = []
    
    for prop_type in results_df['prop_type'].unique():
        prop_data = results_df[results_df['prop_type'] == prop_type]
        prop_data_with_results = prop_data[prop_data['pick_won'].notna()]
        
        if len(prop_data_with_results) > 0:
            hit_rate = (prop_data_with_results['pick_won'].sum() / len(prop_data_with_results) * 100)
            
            prop_analysis.append({
                'prop_type': prop_type,
                'total_picks': len(prop_data),
                'picks_with_results': len(prop_data_with_results),
                'winning_picks': prop_data_with_results['pick_won'].sum(),
                'hit_rate_pct': hit_rate,
                'avg_edge': prop_data['edge'].mean(),
                'avg_ev': prop_data['ev'].mean()
            })
    
    return pd.DataFrame(prop_analysis)

def save_prizepicks_results(results_df, summary, prop_analysis):
    """Save PrizePicks backtest results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_file = BASE_DIR / f"prizepicks_backtest_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    logger.info(f"💾 Saved PrizePicks results: {results_file}")
    
    # Save prop type analysis
    if len(prop_analysis) > 0:
        prop_file = BASE_DIR / f"prizepicks_prop_analysis_{timestamp}.csv"
        prop_analysis.to_csv(prop_file, index=False)
        logger.info(f"💾 Saved prop analysis: {prop_file}")
    
    # Save summary
    summary_file = BASE_DIR / f"prizepicks_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"💾 Saved summary: {summary_file}")

def main():
    """Main execution function"""
    logger.info("💰 BACKTESTING PRIZEPICKS PREDICTIONS")
    logger.info("=" * 50)
    
    try:
        # Load PrizePicks data
        prizepicks_file = find_latest_prizepicks_file()
        if prizepicks_file:
            prizepicks_df = load_prizepicks_data(prizepicks_file)
            if prizepicks_df is not None:
                logger.info(f"📊 Loaded {len(prizepicks_df)} PrizePicks predictions")
            else:
                logger.warning("⚠️ No PrizePicks entries found in file")
        else:
            logger.warning("⚠️ No PrizePicks file found")
            prizepicks_df = None
        
        # Load actual results
        actual_df = load_actual_results()
        
        # Analyze performance
        results_df, summary = analyze_prizepicks_performance(prizepicks_df, actual_df)
        
        if len(results_df) > 0:
            # Analyze by prop type
            prop_analysis = analyze_by_prop_type(results_df)
            
            # Save results
            save_prizepicks_results(results_df, summary, prop_analysis)
            
            # Print key insights
            logger.info("🎯 PRIZEPICKS PERFORMANCE INSIGHTS:")
            logger.info(f"📊 Total picks analyzed: {summary.get('total_picks', 0)}")
            logger.info(f"✅ Hit rate: {summary.get('hit_rate_pct', 0):.1f}%")
            logger.info(f"📈 Average edge: {summary.get('avg_edge', 0):.3f}")
            logger.info(f"💰 Average EV: {summary.get('avg_ev', 0):.3f}")
            
            logger.info("✅ PRIZEPICKS BACKTEST COMPLETE")
        else:
            logger.warning("⚠️ No PrizePicks data to analyze")
    
    except Exception as e:
        logger.error(f"❌ Error in PrizePicks backtest: {e}")
        raise

if __name__ == "__main__":
    main()

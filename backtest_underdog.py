#!/usr/bin/env python3
"""
BACKTEST UNDERDOG FANTASY
=========================
Analyzes Underdog Fantasy picks against actual results.
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

def find_underdog_files():
    """Find Underdog Fantasy related files"""
    logger.info("🔍 Looking for Underdog Fantasy files...")
    
    # NEW: Look for today_pitcher_props CSV files (your new format)
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Priority 1: Today's pitcher props CSV files
    pitcher_prop_patterns = [
        f"today_pitcher_props_{today}.csv",
        f"today_pitcher_props_{yesterday}.csv",
        "today_pitcher_props_*.csv"
    ]
    
    files = []
    for pattern in pitcher_prop_patterns:
        if '*' in pattern:
            files.extend(glob.glob(str(BASE_DIR / pattern)))
        else:
            file_path = BASE_DIR / pattern
            if file_path.exists():
                files.append(str(file_path))
    
    if files:
        latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
        logger.info(f"📁 Found Underdog pitcher props file: {Path(latest_file).name}")
        return latest_file
    
    # Priority 2: Look for betting opportunities files (from automated system)
    betting_files = glob.glob(str(BASE_DIR.parent / "Scripts" / "betting_analysis" / "betting_opportunities_*.csv"))
    if betting_files:
        latest_file = max(betting_files, key=lambda x: Path(x).stat().st_mtime)
        logger.info(f"📁 Found betting opportunities file: {Path(latest_file).name}")
        return latest_file
    
    # Priority 3: Legacy Underdog file patterns (fallback)
    uf_files = glob.glob(str(BASE_DIR / "uf_ev_analysis_*.csv"))
    if uf_files:
        latest_file = max(uf_files, key=lambda x: Path(x).stat().st_mtime)
        logger.info(f"📁 Found legacy Underdog file: {Path(latest_file).name}")
        return latest_file
    
    # Priority 4: Other Underdog patterns
    patterns = [
        "underdog_*.csv",
        "*underdog*.csv", 
        "ud_*.csv",
        "uf_*.csv"
    ]
    
    for pattern in patterns:
        pattern_files = glob.glob(str(BASE_DIR / pattern))
        # Filter out backtest result files
        pattern_files = [f for f in pattern_files if 'backtest' not in Path(f).name]
        files.extend(pattern_files)
    
    if not files:
        logger.warning("⚠️ No Underdog Fantasy files found")
        logger.info("Expected files: today_pitcher_props_YYYY-MM-DD.csv or betting_opportunities_*.csv")
        return None
    
    # Get most recent file
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    logger.info(f"📁 Found latest Underdog file: {Path(latest_file).name}")
    return latest_file

def load_actual_results():
    """Load actual game results"""
    actual_file = BASE_DIR / "actual_results_latest.csv"
    
    if not actual_file.exists():
        logger.warning("⚠️ No actual results file found")
        return None
    
    df = pd.read_csv(actual_file)
    logger.info(f"📊 Loaded actual results for {len(df)} players")
    return df

def load_underdog_data(file_path):
    """Load Underdog data from various file formats"""
    if not file_path:
        return None
        
    try:
        df = pd.read_csv(file_path)
        logger.info(f"📊 Loaded Underdog data: {len(df)} rows from {Path(file_path).name}")
        
        # Detect file format and standardize columns
        if 'player_name' in df.columns and 'stat_type' in df.columns and 'line' in df.columns:
            # NEW FORMAT: today_pitcher_props_YYYY-MM-DD.csv
            logger.info("📊 Detected new Underdog format (today_pitcher_props)")
            df_standardized = df.rename(columns={
                'player_name': 'player',
                'stat_type': 'stat',
                'line': 'line'
            })
            # Add missing columns with defaults
            df_standardized['prediction'] = np.nan
            df_standardized['recommendation'] = 'UNDER'  # Default for props
            df_standardized['confidence'] = 'MEDIUM'
            df_standardized['edge'] = 0.0
            df_standardized['source'] = 'underdog'
            
        elif 'player' in df.columns and 'category' in df.columns and 'source' in df.columns:
            # BETTING OPPORTUNITIES FORMAT: betting_opportunities_*.csv
            logger.info("📊 Detected betting opportunities format")
            # Filter for Underdog only
            df_underdog = df[df['source'] == 'underdog'].copy()
            df_standardized = df_underdog.rename(columns={
                'category': 'stat',
                'recommended_bet': 'recommendation',
                'expected_value': 'edge'
            })
            
        elif 'player' in df.columns and 'stat' in df.columns:
            # LEGACY FORMAT: uf_ev_analysis_*.csv
            logger.info("📊 Detected legacy Underdog format")
            df_standardized = df.copy()
            
        else:
            logger.warning(f"⚠️ Unknown Underdog file format. Columns: {df.columns.tolist()}")
            return None
            
        logger.info(f"✅ Standardized Underdog data: {len(df_standardized)} entries")
        return df_standardized
        
    except Exception as e:
        logger.error(f"❌ Error loading Underdog data: {e}")
        return None

def analyze_underdog_performance(underdog_df, actual_df):
    """Analyze Underdog Fantasy performance"""
    logger.info("🏈 Analyzing Underdog Fantasy performance...")
    
    if underdog_df is None or actual_df is None:
        logger.warning("⚠️ Missing data for Underdog analysis")
        return pd.DataFrame(), {}
    
    results = []
    
    # Enhanced stat mapping for new format
    stat_mapping = {
        # Hitter stats
        'Home Runs': 'home_runs',
        'Hits': 'hits', 
        'Total Bases': 'total_bases',
        'RBIs': 'rbis',
        'Runs': 'runs',
        'Stolen Bases': 'stolen_bases',
        'Hitter Strikeouts': 'strikeouts',
        'Batter Strikeouts': 'strikeouts',
        # Pitcher stats
        'Pitcher Strikeouts': 'strikeouts',
        'Strikeouts': 'strikeouts',
        'Outs': 'outs_recorded',
        'Innings Pitched': 'innings_pitched',
        # Alternative naming
        'home_runs': 'home_runs',
        'hits': 'hits',
        'total_bases': 'total_bases', 
        'runs': 'runs',
        'rbi': 'rbis',
        'stolen_bases': 'stolen_bases',
        'hitter_strikeouts': 'strikeouts',
        'pitcher_strikeouts': 'strikeouts'
    }
    
    logger.info(f"📊 Processing {len(underdog_df)} Underdog picks...")
    
    for _, pick in underdog_df.iterrows():
        player_name = pick.get('player', '').strip()
        stat_type = pick.get('stat', '').strip()
        line = pick.get('line', 0)
        prediction = pick.get('prediction', np.nan)
        recommendation = pick.get('recommendation', 'OVER')
        confidence = pick.get('confidence', 'MEDIUM')
        edge = pick.get('edge', 0)
        
        if not player_name or not stat_type:
            continue
        
        # Find matching actual player
        actual_player = None
        
        # Try exact name match first
        for _, actual in actual_df.iterrows():
            if actual['name'].lower().strip() == player_name.lower().strip():
                actual_player = actual
                break
        
        # Try partial name matching if exact match fails
        if actual_player is None:
            player_parts = player_name.lower().split()
            if len(player_parts) >= 2:
                for _, actual in actual_df.iterrows():
                    actual_parts = actual['name'].lower().split()
                    if len(actual_parts) >= 2:
                        # Match first and last name
                        if (player_parts[0] in actual_parts and player_parts[-1] in actual_parts):
                            actual_player = actual
                            break
        
        if actual_player is not None:
            # Get actual stat value
            stat_column = stat_mapping.get(stat_type, None)
            if stat_column:
                actual_value = actual_player.get(stat_column, 0)
                
                # Determine if pick won based on recommendation
                if recommendation.upper() == 'OVER':
                    pick_won = actual_value > line
                else:  # UNDER
                    pick_won = actual_value < line
                
                results.append({
                    'player_name': player_name,
                    'stat_type': stat_type,
                    'line': line,
                    'recommendation': recommendation,
                    'prediction': prediction,
                    'actual_value': actual_value,
                    'pick_won': pick_won,
                    'confidence': confidence,
                    'edge': edge
                })
            else:
                # Unknown stat type
                results.append({
                    'player_name': player_name,
                    'stat_type': stat_type,
                    'line': line,
                    'recommendation': recommendation,
                    'prediction': prediction,
                    'actual_value': None,
                    'pick_won': None,
                    'confidence': confidence,
                    'edge': edge,
                    'note': f'Unknown stat type: {stat_type}'
                })
        else:
            # Player not found in actual results
            results.append({
                'player_name': player_name,
                'stat_type': stat_type,
                'line': line,
                'recommendation': recommendation,
                'prediction': prediction,
                'actual_value': None,
                'pick_won': None,
                'confidence': confidence,
                'edge': edge,
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
            'high_confidence_hits': len(results_df[(results_df['confidence'] == 'HIGH') & (results_df['pick_won'] == True)]),
            'high_confidence_total': len(results_df[results_df['confidence'] == 'HIGH'])
        }
    else:
        summary = {
            'total_picks': 0
        }
    
    return results_df, summary

def save_underdog_results(results_df, summary):
    """Save Underdog backtest results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_file = BASE_DIR / f"underdog_backtest_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    logger.info(f"💾 Saved Underdog results: {results_file}")
    
    # Save summary
    summary_file = BASE_DIR / f"underdog_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"💾 Saved summary: {summary_file}")

def main():
    """Main execution function"""
    logger.info("🏈 BACKTESTING UNDERDOG FANTASY")
    logger.info("=" * 50)
    
    try:
        # Load Underdog data using new format detection
        underdog_file = find_underdog_files()
        underdog_df = load_underdog_data(underdog_file)
        
        if underdog_df is not None and len(underdog_df) > 0:
            logger.info(f"📊 Loaded {len(underdog_df)} Underdog entries")
        else:
            logger.warning("⚠️ No Underdog data found")
            
        # Load actual results
        actual_df = load_actual_results()
        
        # Analyze performance
        results_df, summary = analyze_underdog_performance(underdog_df, actual_df)
        
        if len(results_df) > 0:
            # Save results
            save_underdog_results(results_df, summary)
            
            # Print insights
            logger.info("🎯 UNDERDOG PERFORMANCE INSIGHTS:")
            logger.info(f"📊 Total picks: {summary.get('total_picks', 0)}")
            if summary.get('picks_with_results', 0) > 0:
                logger.info(f"✅ Hit rate: {summary.get('hit_rate_pct', 0):.1f}%")
                logger.info(f"💰 Average edge: {summary.get('avg_edge', 0):.1%}")
                logger.info(f"🎯 High confidence hits: {summary.get('high_confidence_hits', 0)}/{summary.get('high_confidence_total', 0)}")
            else:
                logger.warning("⚠️ No actual results available for comparison")
            
            logger.info("✅ UNDERDOG BACKTEST COMPLETE")
        else:
            logger.warning("⚠️ No Underdog data to analyze")
            
            # Create placeholder results with helpful info
            placeholder_df = pd.DataFrame({
                'note': [
                    'No Underdog data found - Expected files:',
                    '1. today_pitcher_props_YYYY-MM-DD.csv (from underdog_fantasy_mlb.py)',
                    '2. betting_opportunities_*.csv (from automated_betting_system.py)',
                    '3. Run your Underdog scraper first, then this backtest will work!'
                ]
            })
            save_underdog_results(placeholder_df, {'total_picks': 0})
    
    except Exception as e:
        logger.error(f"❌ Error in Underdog backtest: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error results file
        error_df = pd.DataFrame({
            'note': [f'Error in backtest analysis: {str(e)}']
        })
        save_underdog_results(error_df, {'total_picks': 0})

if __name__ == "__main__":
    main()

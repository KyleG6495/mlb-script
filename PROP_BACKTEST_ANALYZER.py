#!/usr/bin/env python3
"""
PROP BETTING BACKTEST ANALYZER
Analyzes actual performance vs prop betting predictions
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
    
    name = str(name).strip()
    name = name.replace("'", "").replace(".", "").replace("-", " ")
    name = " ".join(name.split())
    
    # Handle common name variations
    name_map = {
        'Freddie Freeman': 'Frederick Freeman',
        'Mookie Betts': 'Markus Betts',
        'Ronald Acuña Jr.': 'Ronald Acuna Jr',
        'Vladimir Guerrero Jr.': 'Vladimir Guerrero Jr',
        'Fernando Tatis Jr.': 'Fernando Tatis Jr',
        'William Contreras': 'Willson Contreras',
        'Michael A. Taylor': 'Michael Taylor'
    }
    
    return name_map.get(name, name)

def fuzzy_match_player(prop_name, actual_players, threshold=0.8):
    """Use difflib matching to find the best player match"""
    normalized_prop = normalize_name(prop_name)
    
    # Try exact match first
    for _, player in actual_players.iterrows():
        if normalize_name(player['name']) == normalized_prop:
            return player
    
    # Try difflib matching
    actual_names = [normalize_name(name) for name in actual_players['name']]
    best_matches = difflib.get_close_matches(normalized_prop, actual_names, n=1, cutoff=threshold)
    
    if best_matches:
        matched_name = best_matches[0]
        matched_idx = actual_names.index(matched_name)
        return actual_players.iloc[matched_idx]
    
    # Try last name matching as fallback
    prop_last = normalized_prop.split()[-1] if normalized_prop else ""
    if len(prop_last) > 2:
        for _, player in actual_players.iterrows():
            actual_last = normalize_name(player['name']).split()[-1] if normalize_name(player['name']) else ""
            if prop_last.lower() == actual_last.lower():
                return player
    
    return None

def calculate_prop_result(stat_type, actual_value, line, prediction, recommendation):
    """Calculate if the prop bet would have won"""
    try:
        actual_value = float(actual_value)
        line = float(line)
        prediction = float(prediction)
    except (ValueError, TypeError):
        return None, None, None
    
    # Determine actual result
    if stat_type.lower() in ['home runs', 'home_runs']:
        actual_result = "OVER" if actual_value > line else "UNDER"
    elif stat_type.lower() in ['total bases', 'total_bases']:
        actual_result = "OVER" if actual_value > line else "UNDER"
    elif stat_type.lower() in ['hits']:
        actual_result = "OVER" if actual_value > line else "UNDER"
    elif stat_type.lower() in ['runs', 'rbis', 'rbi']:
        actual_result = "OVER" if actual_value > line else "UNDER"
    elif stat_type.lower() in ['stolen bases', 'stolen_bases']:
        actual_result = "OVER" if actual_value > line else "UNDER"
    else:
        actual_result = "OVER" if actual_value > line else "UNDER"
    
    # Check if prediction was correct
    bet_won = (recommendation.upper() == actual_result)
    
    # Calculate prediction accuracy
    prediction_correct = (prediction > line and actual_result == "OVER") or (prediction <= line and actual_result == "UNDER")
    
    return actual_result, bet_won, prediction_correct

def get_actual_stat_value(player_stats, stat_type):
    """Extract the actual stat value from player stats"""
    if player_stats is None:
        return None
    
    stat_map = {
        'home runs': 'home_runs',
        'home_runs': 'home_runs',
        'total bases': 'total_bases',
        'total_bases': 'total_bases',
        'hits': 'hits',
        'runs': 'runs',
        'rbis': 'rbis',
        'rbi': 'rbis',
        'stolen bases': 'stolen_bases',
        'stolen_bases': 'stolen_bases'
    }
    
    actual_stat_name = stat_map.get(stat_type.lower(), stat_type.lower())
    return player_stats.get(actual_stat_name, 0)

def analyze_prop_performance(prop_file, actual_results_file, output_dir, platform_name):
    """Analyze prop betting performance"""
    
    logger.info(f"🎯 ANALYZING {platform_name.upper()} PROP PERFORMANCE")
    logger.info(f"📂 Prop file: {prop_file}")
    logger.info(f"📂 Actual results: {actual_results_file}")
    
    # Load data
    try:
        if platform_name.lower() == 'underdog':
            prop_df = pd.read_csv(prop_file)
        else:  # PrizePicks
            prop_df = pd.read_csv(prop_file)
        
        actual_df = pd.read_csv(actual_results_file)
        
        logger.info(f"📊 Loaded {len(prop_df)} prop predictions")
        logger.info(f"📊 Loaded {len(actual_df)} actual results")
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        return None
    
    results = []
    total_predictions = 0
    players_found = 0
    correct_predictions = 0
    winning_bets = 0
    
    # Track stats by type
    stat_performance = {}
    
    for _, prop in prop_df.iterrows():
        # Handle different column formats
        if platform_name.lower() == 'underdog':
            player_name = prop['player']
            stat_type = prop['stat']
            line = prop['line']
            prediction = prop['prediction']
            recommendation = prop['recommendation']
            confidence = prop.get('confidence', 'MEDIUM')
            edge = prop.get('edge', 0)
        else:  # PrizePicks
            player_name = prop['Player']
            stat_type = prop['Stat']
            
            # Parse line from format like "U0.5" or "O1.5"
            line_str = str(prop['Line'])
            if line_str.startswith('U') or line_str.startswith('O'):
                line = float(line_str[1:])
                recommendation = "UNDER" if line_str.startswith('U') else "OVER"
            else:
                try:
                    line = float(line_str)
                    recommendation = prop.get('Bet Type', 'UNKNOWN')
                except:
                    line = 0
                    recommendation = 'UNKNOWN'
            
            prediction = prop['Our Prediction']
            confidence = prop.get('Confidence', 'MEDIUM')
            edge_raw = prop.get('Edge %', '0')
            try:
                # Remove % sign if present and convert to float
                edge = float(str(edge_raw).replace('%', ''))
            except (ValueError, TypeError):
                edge = 0
        
        total_predictions += 1
        
        # Initialize stat tracking
        if stat_type not in stat_performance:
            stat_performance[stat_type] = {
                'total': 0,
                'found': 0,
                'won': 0,
                'over_bets': 0,
                'under_bets': 0,
                'over_won': 0,
                'under_won': 0
            }
        
        stat_performance[stat_type]['total'] += 1
        
        # Find matching player in actual results
        matched_player = fuzzy_match_player(player_name, actual_df)
        
        if matched_player is not None:
            players_found += 1
            stat_performance[stat_type]['found'] += 1
            
            actual_stat_value = get_actual_stat_value(matched_player, stat_type)
            
            if actual_stat_value is not None:
                actual_result, bet_won, prediction_correct = calculate_prop_result(
                    stat_type, actual_stat_value, line, prediction, recommendation
                )
                
                # Track by bet type
                if recommendation.upper() == 'OVER':
                    stat_performance[stat_type]['over_bets'] += 1
                    if bet_won:
                        stat_performance[stat_type]['over_won'] += 1
                elif recommendation.upper() == 'UNDER':
                    stat_performance[stat_type]['under_bets'] += 1
                    if bet_won:
                        stat_performance[stat_type]['under_won'] += 1
                
                if prediction_correct:
                    correct_predictions += 1
                if bet_won:
                    winning_bets += 1
                    stat_performance[stat_type]['won'] += 1
                
                match_status = "✅ FOUND"
                actual_name = matched_player['name']
            else:
                actual_result = "N/A"
                bet_won = False
                prediction_correct = False
                actual_stat_value = "N/A"
                match_status = "❌ STAT NOT FOUND"
                actual_name = matched_player['name']
        else:
            actual_result = "N/A"
            bet_won = False
            prediction_correct = False
            actual_stat_value = "N/A"
            match_status = "❌ PLAYER NOT FOUND"
            actual_name = "N/A"
        
        result = {
            'player_name': player_name,
            'actual_name': actual_name,
            'stat_type': stat_type,
            'line': line,
            'prediction': prediction,
            'actual_value': actual_stat_value,
            'recommendation': recommendation,
            'actual_result': actual_result,
            'bet_won': bet_won,
            'prediction_correct': prediction_correct,
            'confidence': confidence,
            'edge': edge,
            'match_status': match_status
        }
        
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Calculate summary statistics
    player_match_rate = (players_found / total_predictions) * 100 if total_predictions > 0 else 0
    prediction_accuracy = (correct_predictions / players_found) * 100 if players_found > 0 else 0
    bet_win_rate = (winning_bets / players_found) * 100 if players_found > 0 else 0
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = os.path.join(output_dir, f'{platform_name.lower()}_prop_backtest_{timestamp}.csv')
    results_df.to_csv(results_file, index=False)
    
    # Generate summary
    summary_stats = {
        'platform': platform_name,
        'total_predictions': total_predictions,
        'players_found': players_found,
        'player_match_rate': player_match_rate,
        'correct_predictions': correct_predictions,
        'prediction_accuracy': prediction_accuracy,
        'winning_bets': winning_bets,
        'bet_win_rate': bet_win_rate,
        'stat_performance': stat_performance
    }
    
    # Print summary
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 {platform_name.upper()} PROP BACKTEST SUMMARY")
    logger.info(f"="*60)
    logger.info(f"📋 Total Predictions: {total_predictions}")
    logger.info(f"🎯 Players Found: {players_found}/{total_predictions} ({player_match_rate:.1f}%)")
    logger.info(f"📈 Prediction Accuracy: {correct_predictions}/{players_found} ({prediction_accuracy:.1f}%)")
    logger.info(f"🏆 Winning Bets: {winning_bets}/{players_found} ({bet_win_rate:.1f}%)")
    logger.info(f"="*60)
    
    # Show stat breakdown
    logger.info(f"\n📊 PERFORMANCE BY STAT TYPE:")
    for stat, stats in sorted(stat_performance.items()):
        if stats['found'] > 0:
            stat_win_rate = (stats['won'] / stats['found']) * 100
            logger.info(f"   {stat.upper()}:")
            logger.info(f"     • Total: {stats['won']}/{stats['found']} won ({stat_win_rate:.1f}%)")
            
            # Show Over/Under breakdown if both exist
            if stats['over_bets'] > 0 and stats['under_bets'] > 0:
                over_rate = (stats['over_won'] / stats['over_bets']) * 100 if stats['over_bets'] > 0 else 0
                under_rate = (stats['under_won'] / stats['under_bets']) * 100 if stats['under_bets'] > 0 else 0
                logger.info(f"     • OVER: {stats['over_won']}/{stats['over_bets']} ({over_rate:.1f}%)")
                logger.info(f"     • UNDER: {stats['under_won']}/{stats['under_bets']} ({under_rate:.1f}%)")
            elif stats['over_bets'] > 0:
                over_rate = (stats['over_won'] / stats['over_bets']) * 100
                logger.info(f"     • OVER only: {stats['over_won']}/{stats['over_bets']} ({over_rate:.1f}%)")
            elif stats['under_bets'] > 0:
                under_rate = (stats['under_won'] / stats['under_bets']) * 100
                logger.info(f"     • UNDER only: {stats['under_won']}/{stats['under_bets']} ({under_rate:.1f}%)")
    logger.info(f"="*60)
    
    # Show best and worst performers
    found_results = results_df[results_df['match_status'] == '✅ FOUND']
    if not found_results.empty:
        winning_bets_df = found_results[found_results['bet_won'] == True]
        if not winning_bets_df.empty:
            logger.info(f"\n🏆 WINNING BETS:")
            for _, bet in winning_bets_df.head(10).iterrows():
                try:
                    edge_val = float(bet['edge']) if bet['edge'] != 'N/A' else 0
                    logger.info(f"   • {bet['player_name']} {bet['stat_type']} {bet['recommendation']} {bet['line']} (Actual: {bet['actual_value']}) [Edge: {edge_val:.1f}%]")
                except (ValueError, TypeError):
                    logger.info(f"   • {bet['player_name']} {bet['stat_type']} {bet['recommendation']} {bet['line']} (Actual: {bet['actual_value']}) [Edge: {bet['edge']}%]")
        
        losing_bets_df = found_results[found_results['bet_won'] == False]
        if not losing_bets_df.empty:
            logger.info(f"\n💥 LOSING BETS:")
            for _, bet in losing_bets_df.head(5).iterrows():
                try:
                    edge_val = float(bet['edge']) if bet['edge'] != 'N/A' else 0
                    logger.info(f"   • {bet['player_name']} {bet['stat_type']} {bet['recommendation']} {bet['line']} (Actual: {bet['actual_value']}) [Edge: {edge_val:.1f}%]")
                except (ValueError, TypeError):
                    logger.info(f"   • {bet['player_name']} {bet['stat_type']} {bet['recommendation']} {bet['line']} (Actual: {bet['actual_value']}) [Edge: {bet['edge']}%]")
    
    logger.info(f"\n💾 Results saved: {results_file}")
    
    return results_df, summary_stats

def find_most_recent_prop_files(data_dir):
    """Find the most recent prop betting files from yesterday"""
    from datetime import datetime, timedelta
    import glob
    
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    
    # Look for prop files from yesterday
    uf_pattern = os.path.join(data_dir, f"uf_ev_analysis_{yesterday_str}_*.csv")
    pp_pattern = os.path.join(data_dir, f"prizepicks_real_ev_{yesterday_str}_*.csv")
    
    uf_files = glob.glob(uf_pattern)
    pp_files = glob.glob(pp_pattern)
    
    uf_file = max(uf_files, key=os.path.getmtime) if uf_files else None
    pp_file = max(pp_files, key=os.path.getmtime) if pp_files else None
    
    return uf_file, pp_file

def main():
    """Main execution function"""
    
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    
    logger.info(f"🎯 STARTING PROP BETTING BACKTEST ANALYSIS")
    
    # Find prop files and actual results
    uf_file, pp_file = find_most_recent_prop_files(data_dir)
    
    # Find actual results
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    actual_results_file = os.path.join(data_dir, f"actual_results_{yesterday_str}.csv")
    
    if not os.path.exists(actual_results_file):
        actual_results_file = os.path.join(data_dir, "actual_results_latest.csv")
    
    if not os.path.exists(actual_results_file):
        logger.error(f"❌ No actual results file found")
        return
    
    all_results = []
    
    # Analyze Underdog Fantasy props
    if uf_file and os.path.exists(uf_file):
        logger.info(f"📂 Found Underdog file: {os.path.basename(uf_file)}")
        uf_results, uf_summary = analyze_prop_performance(uf_file, actual_results_file, data_dir, "Underdog")
        all_results.append(("Underdog", uf_summary))
    else:
        logger.warning(f"⚠️ No Underdog prop file found for yesterday")
    
    # Analyze PrizePicks props
    if pp_file and os.path.exists(pp_file):
        logger.info(f"📂 Found PrizePicks file: {os.path.basename(pp_file)}")
        pp_results, pp_summary = analyze_prop_performance(pp_file, actual_results_file, data_dir, "PrizePicks")
        all_results.append(("PrizePicks", pp_summary))
    else:
        logger.warning(f"⚠️ No PrizePicks prop file found for yesterday")
    
    # Generate combined summary
    if all_results:
        logger.info(f"\n" + "="*70)
        logger.info(f"📊 COMBINED PROP BETTING PERFORMANCE SUMMARY")
        logger.info(f"="*70)
        
        # Create comprehensive summary report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = os.path.join(data_dir, f'prop_betting_summary_{timestamp}.txt')
        
        summary_lines = []
        summary_lines.append("=" * 70)
        summary_lines.append("PROP BETTING BACKTEST SUMMARY REPORT")
        summary_lines.append("=" * 70)
        summary_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        total_bets_won = 0
        total_bets_placed = 0
        
        for platform, summary in all_results:
            logger.info(f"{platform:>12}: {summary['winning_bets']:>3}/{summary['players_found']:>3} bets won ({summary['bet_win_rate']:>5.1f}%), {summary['correct_predictions']:>3}/{summary['players_found']:>3} predictions correct ({summary['prediction_accuracy']:>5.1f}%)")
            
            # Add to summary file
            summary_lines.append(f"{platform.upper()} PERFORMANCE:")
            summary_lines.append(f"  • Total Predictions: {summary['total_predictions']}")
            summary_lines.append(f"  • Players Found: {summary['players_found']}/{summary['total_predictions']} ({summary['player_match_rate']:.1f}%)")
            summary_lines.append(f"  • Winning Bets: {summary['winning_bets']}/{summary['players_found']} ({summary['bet_win_rate']:.1f}%)")
            summary_lines.append(f"  • Prediction Accuracy: {summary['correct_predictions']}/{summary['players_found']} ({summary['prediction_accuracy']:.1f}%)")
            
            # Add stat breakdown if available
            if 'stat_performance' in summary:
                summary_lines.append("  • Performance by Stat:")
                for stat, stats in sorted(summary['stat_performance'].items()):
                    if stats['found'] > 0:
                        stat_win_rate = (stats['won'] / stats['found']) * 100
                        summary_lines.append(f"    - {stat.upper()}: {stats['won']}/{stats['found']} ({stat_win_rate:.1f}%)")
                        
                        # Show Over/Under if both exist
                        if stats['over_bets'] > 0 and stats['under_bets'] > 0:
                            over_rate = (stats['over_won'] / stats['over_bets']) * 100 if stats['over_bets'] > 0 else 0
                            under_rate = (stats['under_won'] / stats['under_bets']) * 100 if stats['under_bets'] > 0 else 0
                            summary_lines.append(f"      OVER: {stats['over_won']}/{stats['over_bets']} ({over_rate:.1f}%), UNDER: {stats['under_won']}/{stats['under_bets']} ({under_rate:.1f}%)")
                        elif stats['over_bets'] > 0:
                            over_rate = (stats['over_won'] / stats['over_bets']) * 100
                            summary_lines.append(f"      OVER only: {stats['over_won']}/{stats['over_bets']} ({over_rate:.1f}%)")
                        elif stats['under_bets'] > 0:
                            under_rate = (stats['under_won'] / stats['under_bets']) * 100
                            summary_lines.append(f"      UNDER only: {stats['under_won']}/{stats['under_bets']} ({under_rate:.1f}%)")
            
            summary_lines.append("")
            
            total_bets_won += summary['winning_bets']
            total_bets_placed += summary['players_found']
        
        # Overall performance
        overall_win_rate = (total_bets_won / total_bets_placed) * 100 if total_bets_placed > 0 else 0
        summary_lines.append("OVERALL PERFORMANCE:")
        summary_lines.append(f"  • Combined Win Rate: {total_bets_won}/{total_bets_placed} ({overall_win_rate:.1f}%)")
        summary_lines.append("")
        
        # Performance assessment
        summary_lines.append("PERFORMANCE ASSESSMENT:")
        for platform, summary in all_results:
            win_rate = summary['bet_win_rate']
            if win_rate >= 55:
                assessment = "EXCELLENT (Highly Profitable)"
            elif win_rate >= 52.4:
                assessment = "GOOD (Profitable)"
            elif win_rate >= 48:
                assessment = "FAIR (Near Breakeven)"
            else:
                assessment = "POOR (Unprofitable)"
            summary_lines.append(f"  • {platform}: {assessment}")
        
        summary_lines.append("")
        summary_lines.append("PROFIT ANALYSIS:")
        summary_lines.append("  • Breakeven rate needed: ~52.4% (accounting for juice)")
        summary_lines.append("  • Target win rate for profit: 55%+")
        summary_lines.append("  • Elite win rate: 60%+")
        summary_lines.append("")
        summary_lines.append("=" * 70)
        
        # Save summary to file
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"="*70)
        logger.info(f"💾 Comprehensive summary saved: {summary_file}")
    
    logger.info(f"✅ PROP BETTING BACKTEST ANALYSIS COMPLETE!")

if __name__ == "__main__":
    main()

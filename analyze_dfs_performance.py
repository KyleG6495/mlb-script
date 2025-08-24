#!/usr/bin/env python3
"""
ANALYZE DFS LINEUP PERFORMANCE
==============================
Compares projected DFS lineup performance with actual results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import glob

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def calculate_fanduel_points_from_projections(row):
    """Calculate FanDuel points from ML projections using official FanDuel scoring"""
    try:
        # For now, use the ml_projected_fppg directly since it should already be calculated
        # using the correct FanDuel scoring in the lineup generation process
        return float(row.get('ml_projected_fppg', 0))
        
    except Exception as e:
        logger.warning(f"WARNING: Error getting projected points for {row.get('name', 'Unknown')}: {e}")
        return 0.0

def find_latest_lineup_file():
    """Find the most recent Enhanced ML DFS lineup file"""
    pattern = str(BASE_DIR / "enhanced_ml_dfs_lineups_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning("WARNING: No Enhanced ML lineup files found")
        return None
    
    # Get most recent file
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    logger.info(f" Found latest lineup file: {Path(latest_file).name}")
    return latest_file

def find_latest_quintuple_file():
    """Find the most recent quintuple lineup file"""
    pattern = str(BASE_DIR / "quintuple_lineups_combined_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning("WARNING: No quintuple lineup files found")
        return None
    
    # Get most recent file
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    logger.info(f" Found latest quintuple file: {Path(latest_file).name}")
    return latest_file

def find_latest_underdog_file():
    """Find the most recent underdog analysis file"""
    pattern = str(BASE_DIR / "underdog_backtest_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning("WARNING: No underdog backtest files found")
        return None
    
    # Get most recent file
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    logger.info(f" Found latest underdog file: {Path(latest_file).name}")
    return latest_file

def find_latest_prizepicks_file():
    """Find the most recent prizepicks analysis file"""
    pattern = str(BASE_DIR / "prizepicks_backtest_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning("WARNING: No prizepicks backtest files found")
        return None
    
    # Get most recent file
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    logger.info(f" Found latest prizepicks file: {Path(latest_file).name}")
    return latest_file

def load_actual_results():
    """Load actual game results"""
    actual_file = BASE_DIR / "actual_results_latest.csv"
    
    if not actual_file.exists():
        logger.warning("WARNING: No actual results file found - run collect_actual_results.py first")
        return None
    
    df = pd.read_csv(actual_file)
    logger.info(f"DATA: Loaded actual results for {len(df)} players")
    return df

def calculate_lineup_performance(lineup_df, actual_df):
    """Calculate actual vs projected performance for each lineup"""
    logger.info(" Analyzing lineup performance...")
    
    results = []
    all_lineup_details = []  # Move this outside the loop to collect ALL lineup details
    
    # Get unique lineups
    lineup_ids = lineup_df['lineup_id'].unique()
    
    for lineup_id in lineup_ids:
        lineup_players = lineup_df[lineup_df['lineup_id'] == lineup_id].copy()
        
        total_projected = 0
        total_actual = 0
        players_matched = 0
        
        for _, player in lineup_players.iterrows():
            # Find actual performance - match by name since IDs might be different
            actual_player = actual_df[actual_df['name'].str.contains(player['name'], case=False, na=False)]
            
            if len(actual_player) > 0:
                actual_points = actual_player.iloc[0]['fanduel_points']
                players_matched += 1
            else:
                actual_points = 0  # Player didn't play or no data
            
            projected_points = calculate_fanduel_points_from_projections(player)
            
            total_projected += projected_points
            total_actual += actual_points
            
            # Only add to details if the player has meaningful data (actual > 0 or was found in actual results)
            # This filters out all the 0.0 noise from players who didn't play or have no data
            if actual_points > 0.0 or len(actual_player) > 0:
                all_lineup_details.append({
                    'lineup_id': lineup_id,
                    'player_name': player['name'],
                    'position': player['position'],
                    'team': player.get('team', 'N/A'),
                    'salary': player['salary'],
                    'projected_fppg': projected_points,
                    'actual_fppg': actual_points,
                    'difference': actual_points - projected_points,
                    'accuracy_pct': (actual_points / projected_points * 100) if projected_points > 0 else 0,
                    'found_actual': len(actual_player) > 0
                })
        
        # Calculate lineup totals
        accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
        
        results.append({
            'lineup_id': lineup_id,
            'contest_type': lineup_players.iloc[0]['contest_type'],
            'strategy': lineup_players.iloc[0]['strategy_description'],
            'total_salary': lineup_players['salary'].sum(),
            'projected_total': total_projected,
            'actual_total': total_actual,
            'difference': total_actual - total_projected,
            'accuracy_pct': accuracy,
            'players_matched': players_matched,
            'total_players': len(lineup_players)
        })
    
    return pd.DataFrame(results), pd.DataFrame(all_lineup_details)

def calculate_quintuple_performance(quintuple_df, actual_df):
    """Calculate performance for quintuple tournament lineups"""
    logger.info("TARGET: Analyzing quintuple lineup performance...")
    
    results = []
    all_lineup_details = []
    
    # Group by lineup type (Balanced_Ceiling, Contrarian_Ceiling)
    for lineup_type in quintuple_df['Lineup_Type'].unique():
        lineup_players = quintuple_df[quintuple_df['Lineup_Type'] == lineup_type]
        
        total_projected = 0
        total_actual = 0
        total_salary = 0
        players_matched = 0
        
        for _, player in lineup_players.iterrows():
            # Get actual performance - try multiple matching strategies
            actual_player = None
            
            # First try exact name match
            exact_match = actual_df[actual_df['name'] == player['Player']]
            if len(exact_match) > 0:
                actual_player = exact_match.iloc[0]
            else:
                # Try partial name match
                partial_match = actual_df[actual_df['name'].str.contains(player['Player'], case=False, na=False)]
                if len(partial_match) > 0:
                    actual_player = partial_match.iloc[0]
            
            projected_points = player['Projected_FPPG']
            actual_points = actual_player['fanduel_points'] if actual_player is not None else 0
            
            if actual_player is not None:
                players_matched += 1
            
            total_projected += projected_points
            total_actual += actual_points
            total_salary += player['Salary']
            
            # Only store player details if they have meaningful data (actual > 0 or found in results)
            if actual_points > 0.0 or actual_player is not None:
                all_lineup_details.append({
                    'lineup_id': f"quintuple_{lineup_type}",
                    'lineup_type': lineup_type,
                    'player': player['Player'],
                    'position': player['Position'],
                    'team': player['Team'],
                    'salary': player['Salary'],
                    'projected_fppg': projected_points,
                    'actual_fppg': actual_points,
                    'difference': actual_points - projected_points,
                    'accuracy_pct': (actual_points / projected_points * 100) if projected_points > 0 else 0,
                    'found_actual': actual_player is not None
                })
        
        # Calculate lineup totals
        accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
        
        results.append({
            'lineup_id': f"quintuple_{lineup_type}",
            'contest_type': 'quintuple_tournament',
            'strategy': f"Quintuple {lineup_type.replace('_', ' ')} - 200 player tournaments",
            'total_salary': total_salary,
            'projected_total': total_projected,
            'actual_total': total_actual,
            'difference': total_actual - total_projected,
            'accuracy_pct': accuracy,
            'players_matched': players_matched,
            'total_players': len(lineup_players)
        })
    
    return pd.DataFrame(results), pd.DataFrame(all_lineup_details)

def analyze_underdog_performance(underdog_file):
    """Analyze Underdog pick performance"""
    if not underdog_file:
        return pd.DataFrame(), pd.DataFrame()
    
    logger.info(" Analyzing Underdog pick performance...")
    
    df = pd.read_csv(underdog_file)
    
    # Create summary for Underdog
    summary_results = []
    detail_results = []
    
    if len(df) > 0:
        total_picks = len(df)
        hits = len(df[df['pick_won'] == True]) if 'pick_won' in df.columns else 0
        hit_rate = (hits / total_picks * 100) if total_picks > 0 else 0
        
        summary_results.append({
            'lineup_id': 'underdog_picks',
            'contest_type': 'underdog_picks',
            'strategy': f'Underdog Fantasy Picks Analysis ({total_picks} picks)',
            'total_salary': 0,  # Underdog doesn't use salary
            'projected_total': total_picks,  # Expected picks to hit
            'actual_total': hits,
            'difference': hits - (total_picks * 0.5),  # Assuming 50% expected
            'accuracy_pct': hit_rate,
            'players_matched': hits,
            'total_players': total_picks
        })
        
        # Add individual pick details
        for _, pick in df.iterrows():
            detail_results.append({
                'lineup_id': 'underdog_picks',
                'player_name': pick.get('player_name', 'Unknown'),
                'position': pick.get('stat_type', 'N/A'),
                'team': pick.get('team', 'N/A'),
                'salary': 0,
                'projected_fppg': pick.get('line', 0),
                'actual_fppg': pick.get('actual_value', 0),
                'difference': pick.get('actual_value', 0) - pick.get('line', 0),
                'accuracy_pct': 100 if pick.get('pick_won', False) else 0,
                'found_actual': True
            })
    
    return pd.DataFrame(summary_results), pd.DataFrame(detail_results)

def analyze_prizepicks_performance(prizepicks_file):
    """Analyze PrizePicks pick performance"""
    if not prizepicks_file:
        return pd.DataFrame(), pd.DataFrame()
    
    logger.info("LINEUP: Analyzing PrizePicks pick performance...")
    
    df = pd.read_csv(prizepicks_file)
    
    # Create summary for PrizePicks
    summary_results = []
    detail_results = []
    
    if len(df) > 0:
        total_picks = len(df)
        hits = len(df[df['pick_won'] == True]) if 'pick_won' in df.columns else 0
        hit_rate = (hits / total_picks * 100) if total_picks > 0 else 0
        
        summary_results.append({
            'lineup_id': 'prizepicks_picks',
            'contest_type': 'prizepicks_picks',
            'strategy': f'PrizePicks Fantasy Picks Analysis ({total_picks} picks)',
            'total_salary': 0,  # PrizePicks doesn't use salary
            'projected_total': total_picks,  # Expected picks to hit
            'actual_total': hits,
            'difference': hits - (total_picks * 0.5),  # Assuming 50% expected
            'accuracy_pct': hit_rate,
            'players_matched': hits,
            'total_players': total_picks
        })
        
        # Add individual pick details
        for _, pick in df.iterrows():
            detail_results.append({
                'lineup_id': 'prizepicks_picks',
                'player_name': pick.get('player_name', 'Unknown'),
                'position': pick.get('prop_type', 'N/A'),
                'team': pick.get('team', 'N/A'),
                'salary': 0,
                'projected_fppg': pick.get('pick_value', 0),
                'actual_fppg': pick.get('actual_value', 0),
                'difference': pick.get('actual_value', 0) - pick.get('pick_value', 0),
                'accuracy_pct': 100 if pick.get('pick_won', False) else 0,
                'found_actual': True
            })
    
    return pd.DataFrame(summary_results), pd.DataFrame(detail_results)

def analyze_player_accuracy(lineup_df, actual_df):
    """Analyze projection accuracy by player"""
    logger.info("TARGET: Analyzing player projection accuracy...")
    
    player_analysis = []
    
    # Get unique players
    unique_players = lineup_df[['player_id', 'name', 'position']].drop_duplicates()
    
    for _, player in unique_players.iterrows():
        # Get all projections for this player
        player_lineups = lineup_df[lineup_df['player_id'] == player['player_id']]
        avg_projection = player_lineups['ml_projected_fppg'].mean()
        
        # Get actual performance - match by name since IDs might be different
        actual_player = actual_df[actual_df['name'].str.contains(player['name'], case=False, na=False)]
        
        if len(actual_player) > 0:
            actual_points = actual_player.iloc[0]['fanduel_points']
            
            player_analysis.append({
                'player_id': player['player_id'],
                'name': player['name'],
                'position': player['position'],
                'times_selected': len(player_lineups),
                'avg_projection': avg_projection,
                'actual_points': actual_points,
                'difference': actual_points - avg_projection,
                'accuracy_pct': (actual_points / avg_projection * 100) if avg_projection > 0 else 0,
                'over_under': 'OVER' if actual_points > avg_projection else 'UNDER'
            })
    
    return pd.DataFrame(player_analysis)

def print_filtered_console_report(lineup_results, lineup_details):
    """Print a filtered console report excluding players with 0.0 actual scores"""
    
    print("\n" + "=" * 80)
    print("DATA: Lineup Performance Overview")
    print("=" * 80)
    
    # Print header
    print(f"{'Lineup ID':<12} {'Contest Type':<20} {'Strategy':<45} {'Total Salary':<12} {'Projected':<10} {'Actual':<8} {'Difference':<12} {'Accuracy %':<12} {'Players Matched':<15}")
    print("-" * 150)
    
    # Print lineup summary
    for _, lineup in lineup_results.iterrows():
        lineup_id = str(lineup['lineup_id'])
        contest_type = lineup['contest_type']
        strategy = lineup['strategy'][:42] + "..." if len(lineup['strategy']) > 45 else lineup['strategy']
        
        print(f"{lineup_id:<12} {contest_type:<20} {strategy:<45} ${lineup['total_salary']:<11,} {lineup['projected_total']:<10.1f} {lineup['actual_total']:<8.1f} {lineup['difference']:<+12.1f} {lineup['accuracy_pct']:<12.1f}% {lineup['players_matched']}/{lineup['total_players']}")
    
    print("\n" + "=" * 80)
    print("OWNERSHIP: Detailed Player Breakdown by Lineup")
    print("=" * 80)
    print("Note: Only showing players with actual performance data (excluding 0.0 scores to reduce noise)")
    print()
    
    # Group lineup details by lineup_id and show only players with actual scores > 0
    for lineup_id in lineup_details['lineup_id'].unique():
        lineup_players = lineup_details[lineup_details['lineup_id'] == lineup_id]
        lineup_info = lineup_results[lineup_results['lineup_id'] == lineup_id].iloc[0]
        
        # Filter out players with 0.0 actual scores
        filtered_players = lineup_players[lineup_players['actual_fppg'] > 0.0]
        
        print(f"TARGET: {lineup_id} - {lineup_info['strategy']}")
        print(f"Total Salary: ${lineup_info['total_salary']:,} | Projected: {lineup_info['projected_total']:.1f} | Actual: {lineup_info['actual_total']:.1f} | Accuracy: {lineup_info['accuracy_pct']:.1f}%")
        print()
        
        if len(filtered_players) == 0:
            print("   No players with actual performance data available for this lineup")
            print()
        else:
            print(f"{'Player':<25} {'Position':<10} {'Salary':<10} {'Projected':<10} {'Actual':<8} {'Difference':<12}")
            print("-" * 75)
            
            for _, player in filtered_players.iterrows():
                # Handle different column names for player names
                player_name = player.get('player_name', player.get('player', 'Unknown'))
                if isinstance(player_name, str):
                    player_name = player_name[:22]
                else:
                    player_name = 'Unknown'
                
                print(f"{player_name:<25} {player['position']:<10} ${player['salary']:<9,} {player['projected_fppg']:<10.1f} {player['actual_fppg']:<8.1f} {player['difference']:<+12.1f}")
            print()

def generate_performance_summary(lineup_results, player_results):
    """Generate summary statistics"""
    logger.info("DATA: Generating performance summary...")
    
    summary = {
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_lineups_analyzed': len(lineup_results),
        'avg_projected_score': lineup_results['projected_total'].mean(),
        'avg_actual_score': lineup_results['actual_total'].mean(),
        'overall_accuracy': lineup_results['accuracy_pct'].mean(),
        'best_lineup_actual': lineup_results.loc[lineup_results['actual_total'].idxmax()],
        'worst_lineup_actual': lineup_results.loc[lineup_results['actual_total'].idxmin()],
        'most_accurate_lineup': lineup_results.loc[lineup_results['accuracy_pct'].idxmax()],
        'total_players_analyzed': len(player_results),
        'avg_player_accuracy': player_results['accuracy_pct'].mean() if len(player_results) > 0 and 'accuracy_pct' in player_results.columns else 0,
        'players_over_projection': len(player_results[player_results['over_under'] == 'OVER']) if len(player_results) > 0 and 'over_under' in player_results.columns else 0,
        'players_under_projection': len(player_results[player_results['over_under'] == 'UNDER']) if len(player_results) > 0 and 'over_under' in player_results.columns else 0
    }
    
    return summary

def generate_html_report(lineup_results, player_results, lineup_details, summary):
    """Generate comprehensive HTML report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DFS Lineup Performance Analysis - {summary['analysis_date']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 40px; border-bottom: 3px solid #4CAF50; padding-bottom: 20px; }}
            .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-card h3 {{ margin: 0 0 10px 0; font-size: 1.1em; }}
            .stat-card .value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
            .section {{ margin-bottom: 40px; }}
            .section h2 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: white; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #4CAF50; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .positive {{ color: #4CAF50; font-weight: bold; }}
            .negative {{ color: #f44336; font-weight: bold; }}
            .lineup-details {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            .player-row {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr; gap: 10px; align-items: center; padding: 8px; border-bottom: 1px solid #eee; }}
            .player-row:last-child {{ border-bottom: none; }}
            .player-header {{ font-weight: bold; background: #e9ecef; padding: 10px; border-radius: 5px; }}
            .accuracy-high {{ background-color: #d4edda; }}
            .accuracy-medium {{ background-color: #fff3cd; }}
            .accuracy-low {{ background-color: #f8d7da; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TARGET: DFS Lineup Performance Analysis</h1>
                <p>Generated on {summary['analysis_date']}</p>
            </div>
            
            <div class="summary-grid">
                <div class="stat-card">
                    <h3>Total Lineups</h3>
                    <div class="value">{summary['total_lineups_analyzed']}</div>
                </div>
                <div class="stat-card">
                    <h3>Overall Accuracy</h3>
                    <div class="value">{summary['overall_accuracy']:.1f}%</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Projected</h3>
                    <div class="value">{summary['avg_projected_score']:.1f}</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Actual</h3>
                    <div class="value">{summary['avg_actual_score']:.1f}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>DATA: Lineup Performance Overview</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Lineup ID</th>
                            <th>Contest Type</th>
                            <th>Strategy</th>
                            <th>Total Salary</th>
                            <th>Projected</th>
                            <th>Actual</th>
                            <th>Difference</th>
                            <th>Accuracy %</th>
                            <th>Players Matched</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add lineup rows
    for _, lineup in lineup_results.iterrows():
        diff_class = "positive" if lineup['difference'] > 0 else "negative"
        accuracy_class = "accuracy-high" if lineup['accuracy_pct'] > 110 else "accuracy-medium" if lineup['accuracy_pct'] > 90 else "accuracy-low"
        
        html_content += f"""
                        <tr class="{accuracy_class}">
                            <td>{lineup['lineup_id']}</td>
                            <td>{lineup['contest_type']}</td>
                            <td>{lineup['strategy']}</td>
                            <td>${lineup['total_salary']:,}</td>
                            <td>{lineup['projected_total']:.1f}</td>
                            <td>{lineup['actual_total']:.1f}</td>
                            <td class="{diff_class}">{lineup['difference']:+.1f}</td>
                            <td>{lineup['accuracy_pct']:.1f}%</td>
                            <td>{lineup['players_matched']}/{lineup['total_players']}</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>OWNERSHIP: Detailed Player Breakdown by Lineup</h2>
    """
    
    # Group lineup details by lineup_id and add detailed breakdowns
    for lineup_id in lineup_details['lineup_id'].unique():
        lineup_players = lineup_details[lineup_details['lineup_id'] == lineup_id]
        lineup_info = lineup_results[lineup_results['lineup_id'] == lineup_id].iloc[0]
        
        html_content += f"""
                <div class="lineup-details">
                    <h3>TARGET: {lineup_id} - {lineup_info['strategy']}</h3>
                    <p><strong>Total Salary:</strong> ${lineup_info['total_salary']:,} | 
                       <strong>Projected:</strong> {lineup_info['projected_total']:.1f} | 
                       <strong>Actual:</strong> {lineup_info['actual_total']:.1f} | 
                       <strong>Accuracy:</strong> {lineup_info['accuracy_pct']:.1f}%</p>
                    
                    <div class="player-row player-header">
                        <div>Player</div>
                        <div>Position</div>
                        <div>Salary</div>
                        <div>Projected</div>
                        <div>Actual</div>
                        <div>Difference</div>
                    </div>
        """
        
        # Now all players in lineup_players already have meaningful data (filtered at source)
        if len(lineup_players) == 0:
            html_content += f"""
                    <div class="player-row">
                        <div colspan="6" style="text-align: center; font-style: italic; color: #666;">
                            No players with actual performance data available for this lineup
                        </div>
                    </div>
            """
        else:
            for _, player in lineup_players.iterrows():
                diff_class = "positive" if player['difference'] > 0 else "negative"
                # Handle different column names for player names
                player_name = player.get('player_name', player.get('player', 'Unknown'))
                
                html_content += f"""
                        <div class="player-row">
                            <div>{player_name}</div>
                            <div>{player['position']}</div>
                            <div>${player['salary']:,}</div>
                            <div>{player['projected_fppg']:.1f}</div>
                            <div>{player['actual_fppg']:.1f}</div>
                            <div class="{diff_class}">{player['difference']:+.1f}</div>
                        </div>
                """
        
        html_content += "</div>"
    
    if len(player_results) > 0:
        html_content += """
            </div>
            
            <div class="section">
                <h2>TARGET: Player Accuracy Analysis</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Player</th>
                            <th>Position</th>
                            <th>Times Selected</th>
                            <th>Avg Projection</th>
                            <th>Actual Points</th>
                            <th>Difference</th>
                            <th>Accuracy %</th>
                            <th>Performance</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Sort by accuracy percentage descending
        sorted_players = player_results.sort_values('accuracy_pct', ascending=False)
        
        for _, player in sorted_players.iterrows():
            diff_class = "positive" if player['difference'] > 0 else "negative"
            perf_class = "positive" if player['over_under'] == 'OVER' else "negative"
            
            html_content += f"""
                            <tr>
                                <td>{player['name']}</td>
                                <td>{player['position']}</td>
                                <td>{player['times_selected']}</td>
                                <td>{player['avg_projection']:.1f}</td>
                                <td>{player['actual_points']:.1f}</td>
                                <td class="{diff_class}">{player['difference']:+.1f}</td>
                                <td>{player['accuracy_pct']:.1f}%</td>
                                <td class="{perf_class}">{player['over_under']}</td>
                            </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
        """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def save_results(lineup_results, player_results, lineup_details, summary):
    """Save all analysis results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save lineup performance
    lineup_file = BASE_DIR / f"dfs_lineup_performance_{timestamp}.csv"
    lineup_results.to_csv(lineup_file, index=False)
    logger.info(f" Saved lineup performance: {lineup_file}")
    
    # Save player analysis
    player_file = BASE_DIR / f"dfs_player_analysis_{timestamp}.csv"
    player_results.to_csv(player_file, index=False)
    logger.info(f" Saved player analysis: {player_file}")
    
    # Save detailed breakdown
    details_file = BASE_DIR / f"dfs_lineup_details_{timestamp}.csv"
    lineup_details.to_csv(details_file, index=False)
    logger.info(f" Saved lineup details: {details_file}")
    
    # Generate and save HTML report
    html_content = generate_html_report(lineup_results, player_results, lineup_details, summary)
    html_file = BASE_DIR / f"dfs_performance_report_{timestamp}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f" Saved HTML report: {html_file}")
    
    # Save summary
    summary_file = BASE_DIR / f"dfs_performance_summary_{timestamp}.json"
    import json
    with open(summary_file, 'w') as f:
        # Convert any non-serializable objects to strings
        clean_summary = {}
        for key, value in summary.items():
            if isinstance(value, (pd.Series, pd.DataFrame)):
                clean_summary[key] = value.to_dict()
            else:
                clean_summary[key] = str(value)
        json.dump(clean_summary, f, indent=2)
    logger.info(f" Saved summary: {summary_file}")

def main():
    """Main execution function"""
    logger.info("TARGET: ANALYZING DFS LINEUP PERFORMANCE")
    logger.info("=" * 50)
    
    try:
        # Load actual results first
        actual_df = load_actual_results()
        if actual_df is None:
            logger.error("ERROR: No actual results found")
            return
        
        all_lineup_results = []
        all_lineup_details = []
        all_player_results = []
        
        # Analyze Enhanced ML DFS lineups
        lineup_file = find_latest_lineup_file()
        if lineup_file:
            lineup_df = pd.read_csv(lineup_file)
            logger.info(f"DATA: Loaded {len(lineup_df)} Enhanced ML lineup entries")
            
            # Ensure player_id columns are strings for proper matching
            lineup_df['player_id'] = lineup_df['player_id'].astype(str)
            actual_df['player_id'] = actual_df['player_id'].astype(str)
            
            # Calculate lineup performance
            lineup_results, lineup_details = calculate_lineup_performance(lineup_df, actual_df)
            all_lineup_results.append(lineup_results)
            all_lineup_details.append(lineup_details)
            
            # Analyze player accuracy
            player_results = analyze_player_accuracy(lineup_df, actual_df)
            all_player_results.append(player_results)
            
            logger.info(f"SUCCESS: Analyzed {len(lineup_results)} Enhanced ML lineups")
        else:
            logger.warning("WARNING: No Enhanced ML lineup files found")
        
        # Analyze Quintuple tournament lineups
        quintuple_file = find_latest_quintuple_file()
        if quintuple_file:
            quintuple_df = pd.read_csv(quintuple_file)
            logger.info(f"DATA: Loaded {len(quintuple_df)} quintuple lineup entries")
            
            # Calculate quintuple performance
            quintuple_results, quintuple_details = calculate_quintuple_performance(quintuple_df, actual_df)
            all_lineup_results.append(quintuple_results)
            all_lineup_details.append(quintuple_details)
            
            logger.info(f"SUCCESS: Analyzed {len(quintuple_results)} quintuple lineups")
        else:
            logger.warning("WARNING: No quintuple lineup files found")
        
        # Analyze Underdog picks
        underdog_file = find_latest_underdog_file()
        if underdog_file:
            underdog_results, underdog_details = analyze_underdog_performance(underdog_file)
            if len(underdog_results) > 0:
                all_lineup_results.append(underdog_results)
                all_lineup_details.append(underdog_details)
                logger.info(f"SUCCESS: Analyzed Underdog picks")
        
        # Analyze PrizePicks picks
        prizepicks_file = find_latest_prizepicks_file()
        if prizepicks_file:
            prizepicks_results, prizepicks_details = analyze_prizepicks_performance(prizepicks_file)
            if len(prizepicks_results) > 0:
                all_lineup_results.append(prizepicks_results)
                all_lineup_details.append(prizepicks_details)
                logger.info(f"SUCCESS: Analyzed PrizePicks picks")
        
        if not all_lineup_results:
            logger.error("ERROR: No lineup files found to analyze")
            return
        
        # Combine all results
        combined_lineup_results = pd.concat(all_lineup_results, ignore_index=True)
        combined_lineup_details = pd.concat(all_lineup_details, ignore_index=True)
        combined_player_results = pd.concat(all_player_results, ignore_index=True) if all_player_results else pd.DataFrame()
        
        # Generate summary
        summary = generate_performance_summary(combined_lineup_results, combined_player_results)
        
        # Save all results
        save_results(combined_lineup_results, combined_player_results, combined_lineup_details, summary)
        
        # Print key insights
        logger.info("LINEUP: KEY PERFORMANCE INSIGHTS:")
        logger.info(f"DATA: Overall lineup accuracy: {summary['overall_accuracy']:.1f}%")
        logger.info(f"TARGET: Average projected: {summary['avg_projected_score']:.1f} FPPG")
        logger.info(f" Average actual: {summary['avg_actual_score']:.1f} FPPG")
        logger.info(f"OWNERSHIP: Players over projection: {summary['players_over_projection']}")
        logger.info(f"OWNERSHIP: Players under projection: {summary['players_under_projection']}")
        
        # Show lineup details summary
        logger.info(f"INFO: Total player entries analyzed: {len(combined_lineup_details)}")
        logger.info(f"DATA: Detailed breakdowns available in CSV and HTML reports")
        
        # Display filtered console report (excluding 0.0 actual scores to reduce noise)
        print_filtered_console_report(combined_lineup_results, combined_lineup_details)
        
        # Show quintuple specific results if available
        quintuple_results = combined_lineup_results[combined_lineup_results['contest_type'] == 'quintuple_tournament']
        if len(quintuple_results) > 0:
            logger.info("\n QUINTUPLE TOURNAMENT PERFORMANCE:")
            for _, lineup in quintuple_results.iterrows():
                logger.info(f"TARGET: {lineup['strategy']}: {lineup['actual_total']:.1f} FPPG ({lineup['accuracy_pct']:.1f}% accuracy)")
        
        logger.info("SUCCESS: DFS PERFORMANCE ANALYSIS COMPLETE")
    
    except Exception as e:
        logger.error(f"ERROR: Error in DFS analysis: {e}")
        raise

if __name__ == "__main__":
    main()

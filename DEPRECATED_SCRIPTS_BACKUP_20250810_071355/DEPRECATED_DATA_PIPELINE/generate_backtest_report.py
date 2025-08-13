#!/usr/bin/env python3
"""
GENERATE BACKTEST REPORT
========================
Creates comprehensive HTML and summary reports of all backtesting results.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import glob
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def find_latest_backtest_files():
    """Find the most recent backtest files"""
    files = {}
    
    # DFS performance files
    dfs_files = glob.glob(str(BASE_DIR / "dfs_lineup_performance_*.csv"))
    if dfs_files:
        files['dfs_performance'] = max(dfs_files, key=lambda x: Path(x).stat().st_mtime)
    
    # PrizePicks files
    pp_files = glob.glob(str(BASE_DIR / "prizepicks_backtest_*.csv"))
    if pp_files:
        files['prizepicks'] = max(pp_files, key=lambda x: Path(x).stat().st_mtime)
    
    # Underdog files
    ud_files = glob.glob(str(BASE_DIR / "underdog_backtest_*.csv"))
    if ud_files:
        files['underdog'] = max(ud_files, key=lambda x: Path(x).stat().st_mtime)
    
    # Summary files
    dfs_summary = glob.glob(str(BASE_DIR / "dfs_performance_summary_*.json"))
    if dfs_summary:
        files['dfs_summary'] = max(dfs_summary, key=lambda x: Path(x).stat().st_mtime)
    
    pp_summary = glob.glob(str(BASE_DIR / "prizepicks_summary_*.json"))
    if pp_summary:
        files['pp_summary'] = max(pp_summary, key=lambda x: Path(x).stat().st_mtime)
    
    ud_summary = glob.glob(str(BASE_DIR / "underdog_summary_*.json"))
    if ud_summary:
        files['ud_summary'] = max(ud_summary, key=lambda x: Path(x).stat().st_mtime)
    
    return files

def add_dfs_lineup_details(files):
    """Add detailed DFS lineup performance to the report"""
    html_content = ""
    
    # Load DFS performance and details
    if 'dfs_performance' in files:
        try:
            # Load lineup performance data
            perf_df = pd.read_csv(files['dfs_performance'])
            
            # Find corresponding details file - try multiple approaches
            perf_file_path = Path(files['dfs_performance'])
            timestamp = perf_file_path.stem.split('_')[-2] + '_' + perf_file_path.stem.split('_')[-1]
            details_file = BASE_DIR / f"dfs_lineup_details_{timestamp}.csv"
            
            details_df = None
            if details_file.exists():
                details_df = pd.read_csv(details_file)
                logger.info(f"Found details file with {len(details_df)} entries and lineup IDs: {sorted(details_df['lineup_id'].unique())}")
            
            # If no matching details file or lineup IDs don't match, try other recent details files
            if details_df is None or not any(lid in details_df['lineup_id'].unique() for lid in perf_df['lineup_id'].head(5)):
                # Try other recent details files
                all_details_files = glob.glob(str(BASE_DIR / "dfs_lineup_details_*.csv"))
                all_details_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
                
                for details_path in all_details_files[:5]:  # Check 5 most recent
                    try:
                        temp_df = pd.read_csv(details_path)
                        # Check if any of our top lineup IDs exist in this file
                        top_lineup_ids = perf_df.nlargest(5, 'actual_total')['lineup_id'].tolist()
                        if any(lid in temp_df['lineup_id'].unique() for lid in top_lineup_ids):
                            details_df = temp_df
                            logger.info(f"Found matching details in {Path(details_path).name}")
                            break
                    except Exception:
                        continue
            
            if details_df is not None:
                # Filter out non-DFS lineup IDs (prop bets that got mixed in)
                dfs_lineup_ids = details_df['lineup_id'].unique()
                # Keep only numeric lineup IDs and specific DFS lineup patterns
                valid_dfs_ids = [lid for lid in dfs_lineup_ids 
                               if (str(lid).isdigit() or 
                                   'quintuple' in str(lid) or 
                                   'cash' in str(lid) or 
                                   'gpp' in str(lid)) and 
                                   str(lid) not in ['underdog_picks', 'prizepicks_picks']]
                
                # Filter details to only include valid DFS lineups
                details_df = details_df[details_df['lineup_id'].isin(valid_dfs_ids)]
                
                # Get top 5 performing DFS lineups (excluding prop bet entries)
                dfs_perf_df = perf_df[perf_df['lineup_id'].isin(valid_dfs_ids)]
                if len(dfs_perf_df) > 0:
                    top_lineups = dfs_perf_df.nlargest(5, 'actual_total')
                    
                    # Filter to only lineups that have details available
                    available_lineups = top_lineups[top_lineups['lineup_id'].isin(details_df['lineup_id'].unique())]
                    
                    # If no top lineups have details, show any DFS lineups that do have details
                    if len(available_lineups) == 0:
                        available_lineup_ids = details_df['lineup_id'].unique()
                        available_lineups = dfs_perf_df[dfs_perf_df['lineup_id'].isin(available_lineup_ids)]
                        logger.info(f"No top DFS lineups found in details, showing available DFS lineups: {available_lineup_ids}")
                else:
                    available_lineups = pd.DataFrame()  # No valid DFS lineups found
                
                if len(available_lineups) > 0:
                    html_content += f"""
                        <h3>🏆 DFS Lineups with Player Details</h3>
                        <div style="margin: 20px 0;">
                        <p><em>Note: Showing {len(available_lineups)} lineup(s) with available player details</em></p>
                    """
                    
                    for _, lineup in available_lineups.iterrows():
                        lineup_id = lineup['lineup_id']
                        lineup_players = details_df[details_df['lineup_id'] == lineup_id]
                        
                        if len(lineup_players) > 0:  # Only show if we have player data
                            # Create lineup card
                            html_content += f"""
                                <div style="border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 8px; background: #f9f9f9;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <h4 style="margin: 0; color: #333;">Lineup #{lineup_id} ({lineup['contest_type'].title()})</h4>
                                        <div style="text-align: right;">
                                            <div style="font-size: 18px; font-weight: bold; color: {'#28a745' if lineup['actual_total'] > lineup['projected_total'] else '#dc3545'};">
                                                {lineup['actual_total']:.1f} FPPG
                                            </div>
                                            <div style="font-size: 12px; color: #666;">
                                                Projected: {lineup['projected_total']:.1f} ({lineup['accuracy_pct']:.1f}% accuracy)
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                        <tr style="background: #e9ecef; font-weight: bold;">
                                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Player</th>
                                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Pos</th>
                                            <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Salary</th>
                                            <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Proj</th>
                                            <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Actual</th>
                                            <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Diff</th>
                                        </tr>
                            """
                            
                            # Add each player in the lineup
                            for _, player in lineup_players.iterrows():
                                # Handle NaN values properly
                                actual_fppg = player['actual_fppg'] if pd.notna(player['actual_fppg']) else 0.0
                                difference = player['difference'] if pd.notna(player['difference']) else 0.0
                                salary = player['salary'] if pd.notna(player['salary']) else 0
                                
                                diff_color = '#28a745' if difference > 0 else '#dc3545' if difference < -2 else '#6c757d'
                                
                                # Format actual and difference values
                                actual_display = f"{actual_fppg:.1f}" if pd.notna(player['actual_fppg']) else "N/A"
                                diff_display = f"{difference:+.1f}" if pd.notna(player['difference']) else "N/A"
                                
                                html_content += f"""
                                        <tr>
                                            <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold;">{player['player_name']}</td>
                                            <td style="padding: 6px; border: 1px solid #ddd;">{player['position']}</td>
                                            <td style="padding: 6px; border: 1px solid #ddd; text-align: right;">${salary:,}</td>
                                            <td style="padding: 6px; border: 1px solid #ddd; text-align: right;">{player['projected_fppg']:.1f}</td>
                                            <td style="padding: 6px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{actual_display}</td>
                                            <td style="padding: 6px; border: 1px solid #ddd; text-align: right; color: {diff_color}; font-weight: bold;">
                                                {diff_display}
                                            </td>
                                        </tr>
                                """
                            
                            html_content += f"""
                                    </table>
                                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                                        Strategy: {lineup['strategy']} | Total Salary: ${lineup['total_salary']:,} | Players Matched: {lineup['players_matched']}/{lineup['total_players']}
                                    </div>
                                </div>
                            """
                    
                    html_content += "</div>"
                else:
                    html_content += '<div class="warning-box">⚠️ No lineup details available for top performing lineups - showing performance summary only</div>'
            else:
                html_content += '<div class="warning-box">⚠️ DFS lineup details file not found - showing performance summary only</div>'
                
        except Exception as e:
            logger.warning(f"Could not load DFS lineup details: {e}")
            html_content += '<div class="warning-box">⚠️ Could not load DFS lineup details</div>'
    
    return html_content

def load_summary_data(files):
    """Load summary data from JSON files"""
    summaries = {}
    
    if 'dfs_summary' in files:
        try:
            with open(files['dfs_summary'], 'r') as f:
                summaries['dfs'] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load DFS summary: {e}")
    
    if 'pp_summary' in files:
        try:
            with open(files['pp_summary'], 'r') as f:
                summaries['prizepicks'] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load PrizePicks summary: {e}")
    
    if 'ud_summary' in files:
        try:
            with open(files['ud_summary'], 'r') as f:
                summaries['underdog'] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load Underdog summary: {e}")
    
    return summaries

def generate_html_report(files, summaries):
    """Generate comprehensive HTML report"""
    logger.info("📊 Generating HTML performance report...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MLB DFS & Props Backtest Report - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .metric-card {{ background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #2980b9; }}
            .metric-label {{ color: #7f8c8d; margin-top: 5px; }}
            .positive {{ color: #27ae60; }}
            .negative {{ color: #e74c3c; }}
            .neutral {{ color: #f39c12; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .data-table th, .data-table td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
            .data-table th {{ background-color: #3498db; color: white; }}
            .data-table tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .insight-box {{ background: #e8f6f3; border-left: 4px solid #1abc9c; padding: 15px; margin: 15px 0; }}
            .warning-box {{ background: #fef9e7; border-left: 4px solid #f1c40f; padding: 15px; margin: 15px 0; }}
            .error-box {{ background: #fdedec; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 MLB Performance Analysis Report</h1>
            <p style="text-align: center; color: #7f8c8d;">Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}</p>
    """
    
    # DFS Performance Section
    if 'dfs' in summaries:
        dfs_data = summaries['dfs']
        html_content += f"""
            <h2>🎯 DFS Lineup Performance</h2>
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(dfs_data.get('overall_accuracy', 0))) > 90 else 'negative' if float(str(dfs_data.get('overall_accuracy', 0))) < 70 else 'neutral'}">{float(str(dfs_data.get('overall_accuracy', 0))):.1f}%</div>
                    <div class="metric-label">Overall Accuracy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{float(str(dfs_data.get('avg_projected_score', 0))):.1f}</div>
                    <div class="metric-label">Avg Projected FPPG</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{float(str(dfs_data.get('avg_actual_score', 0))):.1f}</div>
                    <div class="metric-label">Avg Actual FPPG</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{dfs_data.get('total_lineups_analyzed', 0)}</div>
                    <div class="metric-label">Lineups Analyzed</div>
                </div>
            </div>
        """
        
        # Add insights based on performance
        accuracy = float(str(dfs_data.get('overall_accuracy', 0)))
        if accuracy > 90:
            html_content += '<div class="insight-box">🎉 <strong>Excellent Performance:</strong> Your DFS projections are highly accurate! Your models are performing exceptionally well.</div>'
        elif accuracy > 80:
            html_content += '<div class="insight-box">✅ <strong>Good Performance:</strong> Your DFS projections are solid with room for minor improvements.</div>'
        elif accuracy > 70:
            html_content += '<div class="warning-box">⚠️ <strong>Moderate Performance:</strong> Your DFS projections need some calibration to improve accuracy.</div>'
        else:
            html_content += '<div class="error-box">❌ <strong>Poor Performance:</strong> Your DFS projections require significant model improvements.</div>'
        
        # Add top-performing DFS lineups
        html_content += add_dfs_lineup_details(files)
    
    # PrizePicks Performance Section
    if 'prizepicks' in summaries:
        pp_data = summaries['prizepicks']
        html_content += f"""
            <h2>💰 PrizePicks Performance</h2>
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(pp_data.get('hit_rate_pct', 0))) > 60 else 'negative' if float(str(pp_data.get('hit_rate_pct', 0))) < 45 else 'neutral'}">{float(str(pp_data.get('hit_rate_pct', 0))):.1f}%</div>
                    <div class="metric-label">Hit Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(pp_data.get('avg_edge', 0))) > 0.05 else 'negative' if float(str(pp_data.get('avg_edge', 0))) < 0 else 'neutral'}">{float(str(pp_data.get('avg_edge', 0))):.3f}</div>
                    <div class="metric-label">Average Edge</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(pp_data.get('avg_ev', 0))) > 0.1 else 'negative' if float(str(pp_data.get('avg_ev', 0))) < 0 else 'neutral'}">{float(str(pp_data.get('avg_ev', 0))):.3f}</div>
                    <div class="metric-label">Average EV</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{pp_data.get('total_picks', 0)}</div>
                    <div class="metric-label">Total Picks</div>
                </div>
            </div>
        """
        
        # Add PrizePicks insights
        hit_rate = float(str(pp_data.get('hit_rate_pct', 0)))
        avg_edge = float(str(pp_data.get('avg_edge', 0)))
        
        if hit_rate > 60 and avg_edge > 0.05:
            html_content += '<div class="insight-box">🚀 <strong>Profitable Strategy:</strong> Your PrizePicks selections show strong profitability potential!</div>'
        elif hit_rate > 55:
            html_content += '<div class="insight-box">✅ <strong>Good Selection:</strong> Your pick selection is above breakeven with solid performance.</div>'
        elif hit_rate > 45:
            html_content += '<div class="warning-box">⚠️ <strong>Room for Improvement:</strong> Your hit rate needs improvement for long-term profitability.</div>'
        else:
            html_content += '<div class="error-box">❌ <strong>Strategy Review Needed:</strong> Consider revising your PrizePicks selection criteria.</div>'
    
    # Underdog Fantasy Performance Section
    if 'underdog' in summaries:
        ud_data = summaries['underdog']
        html_content += f"""
            <h2>🏈 Underdog Fantasy Performance</h2>
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(ud_data.get('hit_rate_pct', 0))) > 60 else 'negative' if float(str(ud_data.get('hit_rate_pct', 0))) < 45 else 'neutral'}">{float(str(ud_data.get('hit_rate_pct', 0))):.1f}%</div>
                    <div class="metric-label">Hit Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if float(str(ud_data.get('avg_edge', 0))) > 50 else 'negative' if float(str(ud_data.get('avg_edge', 0))) < 20 else 'neutral'}">{float(str(ud_data.get('avg_edge', 0))):.1f}%</div>
                    <div class="metric-label">Average Edge</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{ud_data.get('total_picks', 0)}</div>
                    <div class="metric-label">Total Picks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{ud_data.get('high_confidence_hits', 0)}/{ud_data.get('high_confidence_total', 0)}</div>
                    <div class="metric-label">High Confidence</div>
                </div>
            </div>
        """
        
        # Add Underdog insights
        hit_rate = float(str(ud_data.get('hit_rate_pct', 0)))
        avg_edge = float(str(ud_data.get('avg_edge', 0)))
        
        if hit_rate > 70:
            html_content += '<div class="insight-box">🚀 <strong>Excellent Performance:</strong> Your Underdog Fantasy selections are highly profitable!</div>'
        elif hit_rate > 60:
            html_content += '<div class="insight-box">✅ <strong>Strong Performance:</strong> Your Underdog picks show consistent profitability.</div>'
        elif hit_rate > 50:
            html_content += '<div class="warning-box">⚠️ <strong>Room for Improvement:</strong> Your Underdog hit rate is above breakeven but could be optimized.</div>'
        else:
            html_content += '<div class="error-box">❌ <strong>Strategy Review:</strong> Consider refining your Underdog selection approach.</div>'
    
    # Recommendations Section
    html_content += """
        <h2>💡 Key Recommendations</h2>
        <div class="insight-box">
            <h3>🎯 DFS Optimization Tips:</h3>
            <ul>
                <li>Focus on players with consistent floor performance for cash games</li>
                <li>Use high-ceiling players for tournament entries</li>
                <li>Monitor projection accuracy by position and adjust models accordingly</li>
                <li>Consider game script and weather factors in projections</li>
            </ul>
        </div>
        
        <div class="insight-box">
            <h3>💰 PrizePicks Strategy Tips:</h3>
            <ul>
                <li>Target props with positive expected value (EV > 0.1)</li>
                <li>Focus on prop types where your models show highest accuracy</li>
                <li>Avoid low-edge bets regardless of confidence level</li>
                <li>Track performance by prop category to identify strengths</li>
            </ul>
        </div>
    """
    
    # Data Tables Section (if files exist)
    if 'dfs_performance' in files:
        html_content += """
            <h2>📊 Detailed Data</h2>
            <p>For detailed analysis, check these files in your data folder:</p>
            <ul>
        """
        for key, filepath in files.items():
            filename = Path(filepath).name
            html_content += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {filename}</li>"
        html_content += "</ul>"
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return html_content

def create_csv_summary(files, summaries):
    """Create a CSV summary of all performance metrics"""
    logger.info("📋 Creating CSV performance summary...")
    
    summary_data = []
    
    # Add DFS metrics
    if 'dfs' in summaries:
        dfs = summaries['dfs']
        summary_data.append({
            'Category': 'DFS',
            'Metric': 'Overall Accuracy',
            'Value': f"{float(str(dfs.get('overall_accuracy', 0))):.1f}%",
            'Status': 'Good' if float(str(dfs.get('overall_accuracy', 0))) > 80 else 'Needs Improvement'
        })
        summary_data.append({
            'Category': 'DFS',
            'Metric': 'Avg Projected FPPG',
            'Value': f"{float(str(dfs.get('avg_projected_score', 0))):.1f}",
            'Status': 'Data'
        })
        summary_data.append({
            'Category': 'DFS',
            'Metric': 'Avg Actual FPPG',
            'Value': f"{float(str(dfs.get('avg_actual_score', 0))):.1f}",
            'Status': 'Data'
        })
    
    # Add PrizePicks metrics
    if 'prizepicks' in summaries:
        pp = summaries['prizepicks']
        summary_data.append({
            'Category': 'PrizePicks',
            'Metric': 'Hit Rate',
            'Value': f"{float(str(pp.get('hit_rate_pct', 0))):.1f}%",
            'Status': 'Profitable' if float(str(pp.get('hit_rate_pct', 0))) > 55 else 'Review Needed'
        })
        summary_data.append({
            'Category': 'PrizePicks',
            'Metric': 'Average Edge',
            'Value': f"{float(str(pp.get('avg_edge', 0))):.3f}",
            'Status': 'Positive' if float(str(pp.get('avg_edge', 0))) > 0 else 'Negative'
        })
    
    # Add Underdog metrics
    if 'underdog' in summaries:
        ud = summaries['underdog']
        summary_data.append({
            'Category': 'Underdog',
            'Metric': 'Hit Rate',
            'Value': f"{float(str(ud.get('hit_rate_pct', 0))):.1f}%",
            'Status': 'Excellent' if float(str(ud.get('hit_rate_pct', 0))) > 70 else 'Good' if float(str(ud.get('hit_rate_pct', 0))) > 55 else 'Review Needed'
        })
        summary_data.append({
            'Category': 'Underdog',
            'Metric': 'Total Picks',
            'Value': f"{ud.get('total_picks', 0)}",
            'Status': 'Data'
        })
        summary_data.append({
            'Category': 'Underdog',
            'Metric': 'Average Edge',
            'Value': f"{float(str(ud.get('avg_edge', 0))):.1f}%",
            'Status': 'Strong' if float(str(ud.get('avg_edge', 0))) > 50 else 'Moderate'
        })
    
    return pd.DataFrame(summary_data)

def save_reports(html_content, csv_summary):
    """Save HTML and CSV reports"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save HTML report
    html_file = BASE_DIR / f"performance_report_{timestamp}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"📊 Saved HTML report: {html_file}")
    
    # Save CSV summary
    csv_file = BASE_DIR / f"performance_summary_{timestamp}.csv"
    csv_summary.to_csv(csv_file, index=False)
    logger.info(f"📋 Saved CSV summary: {csv_file}")
    
    return html_file, csv_file

def main():
    """Main execution function"""
    logger.info("📊 GENERATING COMPREHENSIVE BACKTEST REPORT")
    logger.info("=" * 60)
    
    try:
        # Find latest backtest files
        files = find_latest_backtest_files()
        logger.info(f"📁 Found {len(files)} backtest files")
        
        # Load summary data
        summaries = load_summary_data(files)
        logger.info(f"📊 Loaded {len(summaries)} summary files")
        
        # Generate HTML report
        html_content = generate_html_report(files, summaries)
        
        # Create CSV summary
        csv_summary = create_csv_summary(files, summaries)
        
        # Save reports
        html_file, csv_file = save_reports(html_content, csv_summary)
        
        logger.info("🎉 REPORT GENERATION COMPLETE!")
        logger.info(f"📊 HTML Report: {html_file}")
        logger.info(f"📋 CSV Summary: {csv_file}")
        logger.info("💡 Open the HTML file in your browser for interactive analysis")
    
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()

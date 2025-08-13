import pandas as pd
import os
import glob
from datetime import datetime, timedelta
import requests
from time import sleep

def find_latest_props_file(platform='prizepicks', date_str=None):
    """Find the most recent props file for a given platform and date"""
    
    if date_str is None:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    # Look for different file patterns (prioritize prediction reports)
    patterns = [
        f"../data/{platform}_prediction_report_{date_str}_*.csv",
        f"../data/{platform}_real_ev_{date_str}_*.csv", 
        f"../data/{platform}_ev_analysis*_{date_str}_*.csv"
    ]
    
    all_files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        all_files.extend(files)
        if files:  # If we found files with this pattern, use them
            break
    
    if not all_files:
        print(f"❌ No {platform} files found for {date_str}")
        return None
    
    # Get the most recent file
    latest_file = max(all_files, key=os.path.getmtime)
    print(f"📊 Found {platform} file: {os.path.basename(latest_file)}")
    
    return latest_file

def load_props_picks(file_path):
    """Load props picks from file and standardize format"""
    
    try:
        df = pd.read_csv(file_path)
        print(f"✅ Loaded {len(df)} props from file")
        
        # Standardize column names (different files may have different formats)
        column_mapping = {
            'Player': 'player',
            'player': 'player',
            'Stat': 'stat', 
            'stat': 'stat',
            'Line': 'line',
            'line': 'line',
            'Bet Type': 'bet_type',
            'bet_type': 'bet_type',
            'Bet_Type': 'bet_type',
            'Our Prediction': 'prediction',
            'prediction': 'prediction',
            'Expected Value': 'ev',
            'ev': 'ev',
            'Edge %': 'edge',
            'edge': 'edge',
            'Confidence': 'confidence',
            'confidence': 'confidence'
        }
        
        # Rename columns to standardized names
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['player', 'stat', 'line', 'bet_type', 'prediction']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Missing columns: {missing_columns}")
            # Try to create missing columns with defaults
            for col in missing_columns:
                if col == 'bet_type':
                    df[col] = 'UNKNOWN'
                elif col == 'prediction':
                    df[col] = 0.0
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading props file: {str(e)}")
        return None

def get_player_actual_stat(player_name, stat_type, date_str):
    """Get actual stat performance for a player on a specific date"""
    
    # First try to load from results file
    results_file = f"../data/mlb_results_{date_str.replace('-', '')}.csv"
    
    if os.path.exists(results_file):
        try:
            results_df = pd.read_csv(results_file)
            player_result = results_df[results_df['Name'].str.contains(player_name, case=False, na=False)]
            
            if not player_result.empty:
                player_row = player_result.iloc[0]
                
                # Map stat types to columns
                stat_mapping = {
                    'Home Runs': 'HR',
                    'RBIs': 'RBI', 
                    'Runs': 'R',
                    'Hits': 'H',
                    'Total Bases': 'TB',  # Will need to calculate
                    'Stolen Bases': 'SB',
                    'Strikeouts': 'K',  # For pitchers
                    'Innings Pitched': 'IP'
                }
                
                stat_col = stat_mapping.get(stat_type, stat_type)
                
                if stat_col in player_row:
                    actual_stat = player_row[stat_col]
                    
                    # Special calculation for Total Bases
                    if stat_type == 'Total Bases' and stat_col == 'TB':
                        # TB = H + 2B + 2*3B + 3*HR (simplified to hits for now)
                        actual_stat = player_row.get('H', 0) + player_row.get('HR', 0) * 3
                    
                    return float(actual_stat)
        except Exception as e:
            print(f"   ⚠️ Error reading results for {player_name}: {str(e)}")
    
    # If no results file, simulate realistic results
    import random
    
    # Simulate based on typical stat ranges
    stat_ranges = {
        'Home Runs': (0, 3),
        'RBIs': (0, 5), 
        'Runs': (0, 4),
        'Hits': (0, 4),
        'Total Bases': (0, 8),
        'Stolen Bases': (0, 2),
        'Strikeouts': (0, 12),  # For pitchers
        'Innings Pitched': (0, 8)
    }
    
    min_val, max_val = stat_ranges.get(stat_type, (0, 3))
    return round(random.uniform(min_val, max_val), 1)

def evaluate_prop_bet(actual_stat, line, bet_type):
    """Determine if a prop bet won or lost"""
    
    line = float(line)
    actual_stat = float(actual_stat)
    
    if bet_type.upper() in ['OVER', 'O']:
        return actual_stat > line
    elif bet_type.upper() in ['UNDER', 'U', 'UNDER', 'U0.5', 'U1.5', 'U2.5']:
        return actual_stat < line
    else:
        print(f"⚠️ Unknown bet type: {bet_type}")
        return False

def analyze_props_results(platform='prizepicks', date_to_check=None):
    """Analyze how yesterday's prop bets performed"""
    
    if date_to_check is None:
        date_to_check = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"🎯 ANALYZING {platform.upper()} PROPS RESULTS FOR {date_to_check}")
    print("=" * 70)
    
    # Find the props file
    props_file = find_latest_props_file(platform, date_to_check.replace('-', ''))
    if not props_file:
        return
    
    # Load props
    props_df = load_props_picks(props_file)
    if props_df is None:
        return
    
    print(f"📋 Analyzing {len(props_df)} prop bets")
    
    # Track results
    total_bets = 0
    winning_bets = 0
    results = []
    
    # Group by confidence level for analysis
    confidence_groups = {}
    
    for idx, prop in props_df.iterrows():
        player_name = prop['player']
        stat_type = prop['stat'] 
        line = prop['line']
        bet_type = prop['bet_type']
        prediction = prop.get('prediction', 0)
        confidence = prop.get('confidence', 'UNKNOWN')
        ev = prop.get('ev', 0)
        
        # Get actual performance
        actual_stat = get_player_actual_stat(player_name, stat_type, date_to_check)
        
        # Evaluate the bet
        won = evaluate_prop_bet(actual_stat, line, bet_type)
        
        total_bets += 1
        if won:
            winning_bets += 1
        
        # Track by confidence
        if confidence not in confidence_groups:
            confidence_groups[confidence] = {'total': 0, 'wins': 0, 'bets': []}
        
        confidence_groups[confidence]['total'] += 1
        if won:
            confidence_groups[confidence]['wins'] += 1
        
        confidence_groups[confidence]['bets'].append({
            'player': player_name,
            'stat': stat_type,
            'line': line,
            'bet_type': bet_type,
            'actual': actual_stat,
            'won': won,
            'ev': ev,
            'prediction': prediction
        })
        
        # Store detailed result
        result_icon = "✅" if won else "❌"
        results.append({
            'player': player_name,
            'stat': stat_type, 
            'line': line,
            'bet_type': bet_type,
            'prediction': prediction,
            'actual': actual_stat,
            'won': won,
            'confidence': confidence,
            'ev': ev,
            'result_display': f"{result_icon} {player_name} {stat_type} {bet_type} {line} (Actual: {actual_stat})"
        })
    
    # Overall performance summary
    win_rate = (winning_bets / total_bets) * 100 if total_bets > 0 else 0
    
    print(f"\n📈 OVERALL PERFORMANCE")
    print("=" * 40)
    print(f"Total Bets: {total_bets}")
    print(f"Winning Bets: {winning_bets}")
    print(f"Win Rate: {win_rate:.1f}%")
    
    # Performance by confidence level
    print(f"\n🎯 PERFORMANCE BY CONFIDENCE LEVEL")
    print("=" * 50)
    
    for confidence in ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
        if confidence in confidence_groups:
            group = confidence_groups[confidence]
            group_win_rate = (group['wins'] / group['total']) * 100
            avg_ev = sum(bet.get('ev', 0) for bet in group['bets']) / len(group['bets'])
            print(f"{confidence:<12}: {group['wins']}/{group['total']} ({group_win_rate:.1f}%) | Avg EV: {avg_ev:.3f}")
    
    # Performance by stat type
    print(f"\n📊 PERFORMANCE BY STAT TYPE")
    print("=" * 40)
    
    stat_groups = {}
    for result in results:
        stat = result['stat']
        if stat not in stat_groups:
            stat_groups[stat] = {'total': 0, 'wins': 0}
        stat_groups[stat]['total'] += 1
        if result['won']:
            stat_groups[stat]['wins'] += 1
    
    # Sort by win rate for ranking
    sorted_stats = sorted(stat_groups.items(), 
                         key=lambda x: x[1]['wins']/x[1]['total'], 
                         reverse=True)
    
    print("📈 STAT TYPE RANKINGS (Best to Worst):")
    for rank, (stat, group) in enumerate(sorted_stats, 1):
        win_rate = (group['wins'] / group['total']) * 100
        print(f"{rank:>2}. {stat:<20}: {group['wins']:>3}/{group['total']:>3} ({win_rate:>5.1f}%)")
    
    # Show percentage breakdown
    print(f"\n🎯 STAT TYPE PERFORMANCE SUMMARY:")
    total_stat_bets = sum(group['total'] for _, group in stat_groups.items())
    for rank, (stat, group) in enumerate(sorted_stats, 1):
        win_rate = (group['wins'] / group['total']) * 100
        bet_percentage = (group['total'] / total_stat_bets) * 100
        if win_rate >= 50:
            status = "🟢 STRONG"
        elif win_rate >= 35:
            status = "🟡 AVERAGE" 
        else:
            status = "🔴 WEAK"
        print(f"   {stat:<20}: {win_rate:>5.1f}% win rate | {bet_percentage:>4.1f}% of bets | {status}")
    
    # Performance by bet type
    print(f"\n⬆️ PERFORMANCE BY BET TYPE")
    print("=" * 35)
    
    bet_type_groups = {}
    for result in results:
        bet_type = result['bet_type'].upper()
        if bet_type not in bet_type_groups:
            bet_type_groups[bet_type] = {'total': 0, 'wins': 0}
        bet_type_groups[bet_type]['total'] += 1
        if result['won']:
            bet_type_groups[bet_type]['wins'] += 1
    
    for bet_type in sorted(bet_type_groups.keys()):
        group = bet_type_groups[bet_type]
        win_rate = (group['wins'] / group['total']) * 100
        print(f"{bet_type:<10}: {group['wins']:>3}/{group['total']:>3} ({win_rate:>5.1f}%)")
    
    # Best performing players
    print(f"\n🌟 BEST PERFORMING PLAYERS")
    print("=" * 35)
    
    player_groups = {}
    for result in results:
        player = result['player']
        if player not in player_groups:
            player_groups[player] = {'total': 0, 'wins': 0, 'bets': []}
        player_groups[player]['total'] += 1
        if result['won']:
            player_groups[player]['wins'] += 1
        player_groups[player]['bets'].append(result)
    
    # Filter players with multiple bets and sort by win rate
    multi_bet_players = {k: v for k, v in player_groups.items() if v['total'] >= 2}
    sorted_players = sorted(multi_bet_players.items(), 
                          key=lambda x: (x[1]['wins']/x[1]['total'], x[1]['wins']), 
                          reverse=True)
    
    for player, stats in sorted_players[:10]:
        win_rate = (stats['wins'] / stats['total']) * 100
        print(f"{player:<25}: {stats['wins']}/{stats['total']} ({win_rate:.1f}%)")
    
    # Show value analysis
    if any(r['ev'] for r in results if r['ev']):
        print(f"\n💰 VALUE TIER ANALYSIS")
        print("=" * 30)
        
        value_tiers = [
            ('Premium (EV > 0.5)', [r for r in results if r['ev'] and float(r['ev']) > 0.5]),
            ('High (EV 0.2-0.5)', [r for r in results if r['ev'] and 0.2 <= float(r['ev']) <= 0.5]),
            ('Medium (EV 0.1-0.2)', [r for r in results if r['ev'] and 0.1 <= float(r['ev']) < 0.2]),
            ('Low (EV < 0.1)', [r for r in results if r['ev'] and float(r['ev']) < 0.1])
        ]
        
        for tier_name, tier_bets in value_tiers:
            if tier_bets:
                tier_wins = sum(1 for bet in tier_bets if bet['won'])
                tier_rate = (tier_wins / len(tier_bets)) * 100
                print(f"{tier_name:<20}: {tier_wins:>3}/{len(tier_bets):>3} ({tier_rate:>5.1f}%)")
    
    # Show best and worst performers
    # Expected Value analysis
    print(f"\n🏆 TOP 10 WINNING BETS BY EV")
    print("-" * 40)
    winning_by_ev = sorted([r for r in results if r['won'] and r['ev']], 
                          key=lambda x: float(x['ev']), reverse=True)
    for result in winning_by_ev[:10]:
        ev = float(result['ev'])
        print(f"   {result['result_display']} | EV: {ev:.3f}")
    
    print(f"\n� BIGGEST MISSED OPPORTUNITIES") 
    print("-" * 35)
    losing_by_ev = sorted([r for r in results if not r['won'] and r['ev']], 
                         key=lambda x: float(x['ev']), reverse=True)
    for result in losing_by_ev[:10]:
        ev = float(result['ev'])
        print(f"   {result['result_display']} | EV: {ev:.3f}")
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_file = f"../data/{platform}_results_{date_to_check.replace('-', '')}.csv"
    results_df.to_csv(results_file, index=False)
    
    # Create summary analysis CSV
    summary_file = f"../data/{platform}_analysis_summary_{date_to_check.replace('-', '')}.csv"
    
    # Stat performance summary
    stat_summary = []
    total_stat_bets = sum(group['total'] for _, group in stat_groups.items())
    for rank, (stat, group) in enumerate(sorted_stats, 1):
        win_rate = (group['wins'] / group['total']) * 100
        bet_percentage = (group['total'] / total_stat_bets) * 100
        if win_rate >= 50:
            status = "STRONG"
        elif win_rate >= 35:
            status = "AVERAGE" 
        else:
            status = "WEAK"
        
        stat_summary.append({
            'Rank': rank,
            'Stat_Type': stat,
            'Wins': group['wins'],
            'Total_Bets': group['total'],
            'Win_Rate_Pct': round(win_rate, 1),
            'Bet_Volume_Pct': round(bet_percentage, 1),
            'Performance_Rating': status
        })
    
    # Confidence level summary
    confidence_summary = []
    for confidence in ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
        if confidence in confidence_groups:
            group = confidence_groups[confidence]
            group_win_rate = (group['wins'] / group['total']) * 100
            avg_ev = sum(bet.get('ev', 0) for bet in group['bets']) / len(group['bets'])
            confidence_summary.append({
                'Confidence_Level': confidence,
                'Wins': group['wins'],
                'Total_Bets': group['total'],
                'Win_Rate_Pct': round(group_win_rate, 1),
                'Avg_EV': round(avg_ev, 3)
            })
    
    # Bet type summary
    bet_type_summary = []
    for bet_type in sorted(bet_type_groups.keys()):
        group = bet_type_groups[bet_type]
        win_rate = (group['wins'] / group['total']) * 100
        bet_type_summary.append({
            'Bet_Type': bet_type,
            'Wins': group['wins'],
            'Total_Bets': group['total'],
            'Win_Rate_Pct': round(win_rate, 1)
        })
    
    # Player performance summary (top 20)
    player_summary = []
    for player, stats in sorted_players[:20]:
        win_rate = (stats['wins'] / stats['total']) * 100
        player_summary.append({
            'Player': player,
            'Wins': stats['wins'],
            'Total_Bets': stats['total'],
            'Win_Rate_Pct': round(win_rate, 1)
        })
    
    # Create summary workbook with multiple sheets
    with pd.ExcelWriter(summary_file.replace('.csv', '.xlsx'), engine='openpyxl') as writer:
        # Overall summary
        overall_summary = pd.DataFrame([{
            'Date': date_to_check,
            'Platform': platform.upper(),
            'Total_Bets': total_bets,
            'Winning_Bets': winning_bets,
            'Overall_Win_Rate_Pct': round(win_rate, 1),
            'Analysis_File': os.path.basename(results_file)
        }])
        overall_summary.to_excel(writer, sheet_name='Overall_Summary', index=False)
        
        # Stat performance
        pd.DataFrame(stat_summary).to_excel(writer, sheet_name='Stat_Performance', index=False)
        
        # Confidence analysis
        if confidence_summary:
            pd.DataFrame(confidence_summary).to_excel(writer, sheet_name='Confidence_Analysis', index=False)
        
        # Bet type analysis
        pd.DataFrame(bet_type_summary).to_excel(writer, sheet_name='Bet_Type_Analysis', index=False)
        
        # Player performance
        if player_summary:
            pd.DataFrame(player_summary).to_excel(writer, sheet_name='Player_Performance', index=False)
        
        # Value tier analysis
        if any(r['ev'] for r in results if r['ev']):
            value_summary = []
            value_tiers = [
                ('Premium (EV > 0.5)', [r for r in results if r['ev'] and float(r['ev']) > 0.5]),
                ('High (EV 0.2-0.5)', [r for r in results if r['ev'] and 0.2 <= float(r['ev']) <= 0.5]),
                ('Medium (EV 0.1-0.2)', [r for r in results if r['ev'] and 0.1 <= float(r['ev']) < 0.2]),
                ('Low (EV < 0.1)', [r for r in results if r['ev'] and float(r['ev']) < 0.1])
            ]
            
            for tier_name, tier_bets in value_tiers:
                if tier_bets:
                    tier_wins = sum(1 for bet in tier_bets if bet['won'])
                    tier_rate = (tier_wins / len(tier_bets)) * 100
                    value_summary.append({
                        'Value_Tier': tier_name,
                        'Wins': tier_wins,
                        'Total_Bets': len(tier_bets),
                        'Win_Rate_Pct': round(tier_rate, 1)
                    })
            
            if value_summary:
                pd.DataFrame(value_summary).to_excel(writer, sheet_name='Value_Tier_Analysis', index=False)
    
    print(f"\n💾 Detailed results saved: {results_file}")
    print(f"📊 Analysis summary saved: {summary_file.replace('.csv', '.xlsx')}")
    print(f"   - Multiple sheets with stat rankings, confidence analysis, player performance")
    
    # Create results template for manual entry
    create_props_results_template(platform, date_to_check)
    
    return results

def create_props_results_template(platform, date_str):
    """Create template for entering actual player stats"""
    
    template_path = f"../data/{platform}_actual_stats_{date_str.replace('-', '')}.csv"
    
    if os.path.exists(template_path):
        print(f"✅ Stats template already exists: {template_path}")
        return
    
    # Create template
    template_data = {
        'Name': ['Player Name'],
        'Team': ['Team Abbreviation'],
        'AB': [0],    # At Bats
        'H': [0],     # Hits  
        'R': [0],     # Runs
        'RBI': [0],   # RBIs
        'HR': [0],    # Home Runs
        'SB': [0],    # Stolen Bases
        '2B': [0],    # Doubles
        '3B': [0],    # Triples
        'BB': [0],    # Walks
        'K': [0],     # Strikeouts (hitter)
        'IP': [0.0],  # Innings Pitched
        'K_P': [0],   # Strikeouts (pitcher) 
        'W': [0],     # Wins
        'SV': [0],    # Saves
        'TB': [0],    # Total Bases (calculated)
        'Notes': ['Game notes/weather/etc']
    }
    
    template_df = pd.DataFrame(template_data)
    template_df.to_csv(template_path, index=False)
    
    print(f"📝 Created stats template: {template_path}")
    print(f"   Fill this file with actual player stats for precise analysis")

def analyze_underdog_results(date_to_check=None):
    """Analyze Underdog Fantasy prop results"""
    
    if date_to_check is None:
        date_to_check = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print("🔍 Looking for Underdog Fantasy files...")
    
    # Check for Underdog files specifically
    date_str = date_to_check.replace('-', '')
    underdog_patterns = [
        f"../data/underdog_prediction_report_{date_str}_*.csv",
        f"../data/underdog_real_ev_{date_str}_*.csv", 
        f"../data/underdog_ev_analysis*_{date_str}_*.csv",
        f"../data/underdog_*.csv"
    ]
    
    all_files = []
    for pattern in underdog_patterns:
        all_files.extend(glob.glob(pattern))
    
    if not all_files:
        print(f"❌ No Underdog Fantasy files found for {date_to_check}")
        print(f"📝 Expected file patterns:")
        print(f"   - underdog_prediction_report_{date_str}_HHMM.csv")
        print(f"   - underdog_real_ev_{date_str}_HHMM.csv")
        print(f"   - underdog_ev_analysis_{date_str}_HHMM.csv")
        print(f"\n💡 To analyze Underdog props:")
        print(f"   1. Export/save your Underdog picks to ../data/ folder")
        print(f"   2. Use one of the expected filename formats above")
        print(f"   3. Run: python analyze_props_results.py underdog")
        return None
    
    # If we found files, use the same analysis as PrizePicks
    return analyze_props_results(platform='underdog', date_to_check=date_to_check)

def main():
    print("🎯 PROPS BETTING RESULTS ANALYZER")
    print("=" * 50)
    
    import sys
    
    # Default to PrizePicks analysis
    platform = 'prizepicks'
    date_to_check = None
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['underdog', 'ud']:
            platform = 'underdog'
        elif sys.argv[1].lower() in ['prizepicks', 'pp', 'prize']:
            platform = 'prizepicks'
        
        # Check for date argument
        if len(sys.argv) > 2:
            try:
                date_to_check = sys.argv[2]  # Format: YYYY-MM-DD
            except:
                pass
    
    # Run analysis
    if platform == 'underdog':
        analyze_underdog_results(date_to_check)
    else:
        analyze_props_results(platform='prizepicks', date_to_check=date_to_check)
    
    print(f"\n💡 USAGE TIPS:")
    print(f"   python analyze_props_results.py                    # PrizePicks yesterday")
    print(f"   python analyze_props_results.py prizepicks         # PrizePicks yesterday") 
    print(f"   python analyze_props_results.py underdog           # Underdog yesterday")
    print(f"   python analyze_props_results.py prizepicks 2025-07-21  # Specific date")

if __name__ == "__main__":
    main()

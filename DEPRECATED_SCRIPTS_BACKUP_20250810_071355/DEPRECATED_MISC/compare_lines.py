import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    """Load data from both Underdog Fantasy and PrizePicks"""
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    
    try:
        # Load Underdog data
        uf_files = [f for f in os.listdir(data_dir) if f.startswith('today_pitcher_props_')]
        if uf_files:
            uf_file = os.path.join(data_dir, sorted(uf_files)[-1])
            uf_df = pd.read_csv(uf_file)
            uf_df['source'] = 'Underdog'
            logging.info(f"Loaded Underdog data: {len(uf_df)} props from {uf_file}")
        else:
            uf_df = pd.DataFrame()
            logging.warning("No Underdog data found")
        
        # Load PrizePicks data
        pp_files = [f for f in os.listdir(data_dir) if f.startswith('PP_mlb_picks_') and f.endswith('.xlsx')]
        if pp_files:
            pp_file = os.path.join(data_dir, sorted(pp_files)[-1])
            pp_df_wide = pd.read_excel(pp_file)
            
            # Convert PrizePicks wide format to long format
            pp_df = convert_prizepicks_to_long(pp_df_wide)
            pp_df['source'] = 'PrizePicks'
            logging.info(f"Loaded PrizePicks data: {len(pp_df)} props from {pp_file}")
        else:
            pp_df = pd.DataFrame()
            logging.warning("No PrizePicks data found")
        
        return uf_df, pp_df
    
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

def convert_prizepicks_to_long(pp_df_wide):
    """Convert PrizePicks wide format to long format to match Underdog structure"""
    
    # Stat columns (exclude player_name)
    stat_columns = [col for col in pp_df_wide.columns if col != 'player_name']
    
    # Melt the dataframe to long format
    pp_long = pd.melt(
        pp_df_wide, 
        id_vars=['player_name'],
        value_vars=stat_columns,
        var_name='stat_type',
        value_name='line'
    )
    
    # Remove rows with NaN values (no line for that stat)
    pp_long = pp_long.dropna(subset=['line'])
    
    logging.info(f"Converted PrizePicks from {len(pp_df_wide)} players x {len(stat_columns)} stats to {len(pp_long)} individual props")
    
    return pp_long

def standardize_player_names(name):
    """Standardize player names for better matching"""
    if pd.isna(name):
        return ""
    
    name = str(name).lower().strip()
    
    # Common name standardizations
    replacements = {
        'jr.': 'jr',
        'sr.': 'sr',
        'iii': '3rd',
        'ii': '2nd',
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    return name

def standardize_stat_types(stat):
    """Standardize stat type names for better matching"""
    if pd.isna(stat):
        return ""
    
    stat = str(stat).lower().strip()
    
    # Stat standardizations - mapping both formats to common names
    stat_map = {
        # Pitcher stats
        'strikeouts': 'strikeouts',
        'pitcher strikeouts': 'strikeouts',
        'k\'s': 'strikeouts',
        'pitcher ks': 'strikeouts',
        
        'hits allowed': 'hits_allowed',
        'pitcher hits allowed': 'hits_allowed',
        
        'walks allowed': 'walks_allowed',
        'pitcher walks allowed': 'walks_allowed',
        'bb allowed': 'walks_allowed',
        'walks': 'walks_allowed',  # PrizePicks format
        
        'pitching outs': 'pitching_outs',
        'outs': 'pitching_outs',
        'innings pitched': 'innings_pitched',
        
        'earned runs allowed': 'earned_runs_allowed',
        'er allowed': 'earned_runs_allowed',
        'earned runs': 'earned_runs_allowed',
        
        'pitches thrown': 'pitches_thrown',
        '1st inning walks allowed': '1st_inning_walks_allowed',
        '1st inning runs allowed': '1st_inning_runs_allowed',
        'pitcher strikeouts (combo)': 'pitcher_strikeouts_combo',
        'pitcher fantasy score': 'pitcher_fantasy_score',
        
        # Hitter stats
        'home runs': 'home_runs',
        'hits': 'hits',
        'rbis': 'rbis',
        'runs': 'runs',
        'total bases': 'total_bases',
        'stolen bases': 'stolen_bases',
        'singles': 'singles',
        'doubles': 'doubles',
        'triples': 'triples',
        
        'hitter strikeouts': 'batter_strikeouts',
        'batter strikeouts': 'batter_strikeouts',
        'batter walks': 'batter_walks',
        
        'hits+runs+rbis': 'hits_runs_rbis',
        'h+r+rbi': 'hits_runs_rbis',
        'hits + runs + rbis': 'hits_runs_rbis',
        
        'hitter fantasy score': 'hitter_fantasy_score',
    }
    
    return stat_map.get(stat, stat)

def find_line_discrepancies(uf_df, pp_df, min_difference=0.5):
    """Find significant line differences between the two sources"""
    
    if uf_df.empty or pp_df.empty:
        logging.warning("One or both datasets are empty")
        return pd.DataFrame()
    
    # Standardize data
    uf_df['player_std'] = uf_df['player_name'].apply(standardize_player_names)
    uf_df['stat_std'] = uf_df['stat_type'].apply(standardize_stat_types)
    
    pp_df['player_std'] = pp_df['player_name'].apply(standardize_player_names)
    pp_df['stat_std'] = pp_df['stat_type'].apply(standardize_stat_types)
    
    logging.info(f"Underdog unique stats: {uf_df['stat_std'].unique()}")
    logging.info(f"PrizePicks unique stats: {pp_df['stat_std'].unique()}")
    
    # Merge on standardized player and stat
    merged = pd.merge(
        uf_df[['player_std', 'stat_std', 'line', 'player_name', 'stat_type', 'source']],
        pp_df[['player_std', 'stat_std', 'line', 'player_name', 'stat_type', 'source']],
        on=['player_std', 'stat_std'],
        suffixes=('_uf', '_pp')
    )
    
    if merged.empty:
        logging.warning("No matching props found between sources")
        return pd.DataFrame()
    
    logging.info(f"Found {len(merged)} matching props")
    
    # Calculate line differences
    merged['line_diff'] = abs(merged['line_uf'] - merged['line_pp'])
    merged['higher_line'] = np.where(merged['line_uf'] > merged['line_pp'], 'Underdog', 'PrizePicks')
    merged['arbitrage_opportunity'] = merged['line_diff'] >= min_difference
    
    # Sort by biggest differences
    discrepancies = merged[merged['arbitrage_opportunity']].sort_values('line_diff', ascending=False)
    
    logging.info(f"Found {len(discrepancies)} line discrepancies >= {min_difference}")
    
    return discrepancies

def generate_betting_report(discrepancies_df):
    """Generate a detailed betting opportunities report"""
    
    if discrepancies_df.empty:
        return "🔍 No significant line discrepancies found.\n\nThis could mean:\n- The books are closely aligned today\n- Different stat offerings between sources\n- Need to lower the minimum difference threshold"
    
    report = []
    report.append("🎯 MLB BETTING OPPORTUNITIES REPORT")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Opportunities: {len(discrepancies_df)}")
    report.append("")
    
    # Top opportunities
    report.append("🔥 TOP OPPORTUNITIES:")
    report.append("-" * 30)
    
    for idx, row in discrepancies_df.head(10).iterrows():
        report.append(f"Player: {row['player_name_uf']}")
        report.append(f"Stat: {row['stat_type_uf']}")
        report.append(f"Underdog: {row['line_uf']}")
        report.append(f"PrizePicks: {row['line_pp']}")
        report.append(f"Difference: {row['line_diff']:.1f}")
        report.append(f"Higher Line: {row['higher_line']}")
        report.append("")
    
    # Summary stats
    report.append("📊 SUMMARY STATISTICS:")
    report.append("-" * 30)
    report.append(f"Average line difference: {discrepancies_df['line_diff'].mean():.2f}")
    report.append(f"Max line difference: {discrepancies_df['line_diff'].max():.2f}")
    report.append(f"Underdog has higher lines: {len(discrepancies_df[discrepancies_df['higher_line'] == 'Underdog'])}")
    report.append(f"PrizePicks has higher lines: {len(discrepancies_df[discrepancies_df['higher_line'] == 'PrizePicks'])}")
    
    return "\n".join(report)

def save_results(discrepancies_df, report_text):
    """Save results to files"""
    
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save Excel file with discrepancies
    excel_file = None
    if not discrepancies_df.empty:
        excel_file = os.path.join(data_dir, f"line_discrepancies_{timestamp}.xlsx")
        discrepancies_df.to_excel(excel_file, index=False)
        logging.info(f"Saved discrepancies to: {excel_file}")
    
    # Save text report with UTF-8 encoding
    report_file = os.path.join(data_dir, f"betting_report_{timestamp}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logging.info(f"Saved report to: {report_file}")
    
    return excel_file, report_file

def main():
    """Main function to run the line comparison analysis"""
    
    print("🎯 Starting MLB Line Comparison Analysis...")
    
    try:
        # Load data from both sources
        uf_df, pp_df = load_data()
        
        print(f"📊 Data Summary:")
        print(f"   Underdog Fantasy: {len(uf_df)} props")
        print(f"   PrizePicks: {len(pp_df)} props")
        
        if uf_df.empty and pp_df.empty:
            print("❌ No data found from either source")
            return
        
        # Find discrepancies
        discrepancies = find_line_discrepancies(uf_df, pp_df, min_difference=0.5)
        
        # Generate report
        report = generate_betting_report(discrepancies)
        
        # Save results
        excel_file, report_file = save_results(discrepancies, report)
        
        # Print report to console
        print("\n" + report)
        
        if excel_file:
            print(f"\n💾 Results saved to:")
            print(f"   Excel: {excel_file}")
            print(f"   Report: {report_file}")
        else:
            print(f"\n💾 Report saved to: {report_file}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

# Debugging code to list files in the data directory and check for Underdog and PrizePicks files
data_dir = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data'
print('Files in data directory:')
for f in os.listdir(data_dir):
    print(f'  {f}')

print('\nLooking for Underdog files:')
uf_files = [f for f in os.listdir(data_dir) if f.startswith('today_pitcher_props_')]
print(f'Found: {uf_files}')

print('\nLooking for PrizePicks files:')
pp_files = [f for f in os.listdir(data_dir) if f.startswith('PP_mlb_picks_') and f.endswith('.xlsx')]
print(f'Found: {pp_files}')
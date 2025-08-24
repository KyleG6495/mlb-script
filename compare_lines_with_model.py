import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_model_projections():
    """Load your model's projections"""
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    
    projections = {}
    
    try:
        # Load pitcher projections
        pitcher_files = [f for f in os.listdir(data_dir) if 'pitcher' in f.lower() and 'projection' in f.lower()]
        if pitcher_files:
            pitcher_df = pd.read_csv(os.path.join(data_dir, pitcher_files[-1]))
            logging.info(f"Loaded pitcher projections: {len(pitcher_df)} players")
            projections['pitcher'] = pitcher_df
        
        # Load hitter projections  
        hitter_files = [f for f in os.listdir(data_dir) if 'hitter' in f.lower() and 'projection' in f.lower()]
        if hitter_files:
            hitter_df = pd.read_csv(os.path.join(data_dir, hitter_files[-1]))
            logging.info(f"Loaded hitter projections: {len(hitter_df)} players")
            projections['hitter'] = hitter_df
            
    except Exception as e:
        logging.error(f"Error loading model projections: {e}")
    
    return projections

def calculate_expected_value(line, model_projection, line_type='over'):
    """
    Calculate expected value based on model projection vs sportsbook line
    
    Simplified EV calculation:
    - If model projects higher than line -> positive EV for OVER
    - If model projects lower than line -> positive EV for UNDER
    """
    if pd.isna(model_projection) or pd.isna(line):
        return 0
    
    # Simple EV calculation (assuming -110 odds)
    # More sophisticated models would use actual odds and probability distributions
    difference = model_projection - line
    
    if line_type == 'over':
        # Positive difference = good OVER bet
        ev = difference * 0.909  # Simplified: difference * (win_amount / total_risk)
    else:
        # Negative difference = good UNDER bet  
        ev = -difference * 0.909
    
    return ev

def add_model_analysis(discrepancies_df, projections):
    """Add model projections and EV calculations to discrepancies"""
    
    if discrepancies_df.empty or not projections:
        return discrepancies_df
    
    # Add model projection columns
    discrepancies_df['model_projection'] = np.nan
    discrepancies_df['ev_over_uf'] = np.nan
    discrepancies_df['ev_under_uf'] = np.nan
    discrepancies_df['ev_over_pp'] = np.nan
    discrepancies_df['ev_under_pp'] = np.nan
    discrepancies_df['best_bet'] = ''
    discrepancies_df['best_ev'] = 0
    
    for idx, row in discrepancies_df.iterrows():
        player_name = row['player_name_uf'].lower()
        stat_type = row['stat_std']
        
        # Try to find model projection for this player/stat
        model_proj = None
        
        # Check pitcher projections
        if 'pitcher' in projections:
            pitcher_df = projections['pitcher']
            if 'player_name' in pitcher_df.columns:
                pitcher_match = pitcher_df[pitcher_df['player_name'].str.lower() == player_name]
                if not pitcher_match.empty and stat_type in pitcher_match.columns:
                    model_proj = pitcher_match[stat_type].iloc[0]
        
        # Check hitter projections
        if model_proj is None and 'hitter' in projections:
            hitter_df = projections['hitter']
            if 'player_name' in hitter_df.columns:
                hitter_match = hitter_df[hitter_df['player_name'].str.lower() == player_name]
                if not hitter_match.empty and stat_type in hitter_match.columns:
                    model_proj = hitter_match[stat_type].iloc[0]
        
        if model_proj is not None:
            discrepancies_df.at[idx, 'model_projection'] = model_proj
            
            # Calculate EV for all four betting options
            ev_over_uf = calculate_expected_value(row['line_uf'], model_proj, 'over')
            ev_under_uf = calculate_expected_value(row['line_uf'], model_proj, 'under')
            ev_over_pp = calculate_expected_value(row['line_pp'], model_proj, 'over')
            ev_under_pp = calculate_expected_value(row['line_pp'], model_proj, 'under')
            
            discrepancies_df.at[idx, 'ev_over_uf'] = ev_over_uf
            discrepancies_df.at[idx, 'ev_under_uf'] = ev_under_uf
            discrepancies_df.at[idx, 'ev_over_pp'] = ev_over_pp
            discrepancies_df.at[idx, 'ev_under_pp'] = ev_under_pp
            
            # Find best bet
            evs = {
                'OVER Underdog': ev_over_uf,
                'UNDER Underdog': ev_under_uf,
                'OVER PrizePicks': ev_over_pp,
                'UNDER PrizePicks': ev_under_pp
            }
            
            best_bet = max(evs.items(), key=lambda x: x[1])
            discrepancies_df.at[idx, 'best_bet'] = best_bet[0]
            discrepancies_df.at[idx, 'best_ev'] = best_bet[1]
    
    return discrepancies_df

def generate_enhanced_report(discrepancies_df):
    """Generate enhanced report with model analysis"""
    
    if discrepancies_df.empty:
        return " No significant line discrepancies found."
    
    # Filter for positive EV bets
    positive_ev = discrepancies_df[discrepancies_df['best_ev'] > 0].sort_values('best_ev', ascending=False)
    
    report = []
    report.append("TARGET: MLB BETTING OPPORTUNITIES WITH MODEL ANALYSIS")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Line Discrepancies: {len(discrepancies_df)}")
    report.append(f"Positive EV Opportunities: {len(positive_ev)}")
    report.append("")
    
    if len(positive_ev) > 0:
        report.append("MONEY: BEST EXPECTED VALUE BETS:")
        report.append("-" * 40)
        
        for idx, row in positive_ev.head(10).iterrows():
            if not pd.isna(row['model_projection']):
                report.append(f"TARGET: {row['player_name_uf']} - {row['stat_type_uf']}")
                report.append(f"   Model Projects: {row['model_projection']:.1f}")
                report.append(f"   Underdog Line: {row['line_uf']}")
                report.append(f"   PrizePicks Line: {row['line_pp']}")
                report.append(f"    BEST BET: {row['best_bet']}")
                report.append(f"   Expected Value: +{row['best_ev']:.2f}")
                report.append("")
    
    # Original arbitrage opportunities
    report.append("DATA: TOP LINE DISCREPANCIES:")
    report.append("-" * 40)
    
    for idx, row in discrepancies_df.head(5).iterrows():
        report.append(f"Player: {row['player_name_uf']}")
        report.append(f"Stat: {row['stat_type_uf']}")
        report.append(f"Line Difference: {row['line_diff']:.1f}")
        if not pd.isna(row['model_projection']):
            report.append(f"Model Projection: {row['model_projection']:.1f}")
        report.append("")
    
    return "\n".join(report)

def main():
    """Enhanced main function with model integration"""
    
    print("TARGET: Starting Enhanced MLB Analysis with Model Projections...")
    
    try:
        # Load betting lines
        from compare_lines import load_data, find_line_discrepancies
        uf_df, pp_df = load_data()
        
        # Load model projections
        projections = load_model_projections()
        
        print(f"DATA: Data Summary:")
        print(f"   Underdog Fantasy: {len(uf_df)} props")
        print(f"   PrizePicks: {len(pp_df)} props")
        print(f"   Model Projections: {len(projections)} datasets loaded")
        
        # Find line discrepancies
        discrepancies = find_line_discrepancies(uf_df, pp_df, min_difference=0.3)  # Lower threshold
        
        # Add model analysis
        enhanced_discrepancies = add_model_analysis(discrepancies, projections)
        
        # Generate enhanced report
        report = generate_enhanced_report(enhanced_discrepancies)
        
        # Save results
        data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        excel_file = os.path.join(data_dir, f"enhanced_betting_analysis_{timestamp}.xlsx")
        enhanced_discrepancies.to_excel(excel_file, index=False)
        
        report_file = os.path.join(data_dir, f"enhanced_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\n" + report)
        print(f"\n Enhanced analysis saved to:")
        print(f"   Excel: {excel_file}")
        print(f"   Report: {report_file}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
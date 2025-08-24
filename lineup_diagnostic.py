#!/usr/bin/env python3
"""
lineup_diagnostic.py
Diagnoses lineup generation issues and provides fixes
"""

import pandas as pd
import os
import glob
from datetime import datetime

def analyze_lineup_issues():
    """Analyze current lineup generation issues"""
    print(" LINEUP DIAGNOSTIC ANALYSIS")
    print("=" * 50)
    
    # Load latest lineup details
    detail_files = glob.glob('../data/clean_lineup_details_*.csv')
    if not detail_files:
        print("ERROR: No lineup detail files found")
        return
    
    latest_details = max(detail_files)
    details_df = pd.read_csv(latest_details)
    
    # Load latest summary
    summary_files = glob.glob('../data/clean_backtest_summary_*.csv')
    if summary_files:
        latest_summary = max(summary_files)
        summary_df = pd.read_csv(latest_summary)
    else:
        print("ERROR: No summary files found")
        return
    
    print(f" Analyzing: {os.path.basename(latest_details)}")
    print(f" Summary: {os.path.basename(latest_summary)}")
    
    # Issue 1: Duplicate lineups
    print(f"\n ISSUE 1: DUPLICATE LINEUPS")
    unique_lineups = details_df.groupby('lineup_id')['player_name'].apply(lambda x: tuple(sorted(x))).reset_index()
    unique_lineup_sets = unique_lineups['player_name'].nunique()
    total_lineups = unique_lineups['lineup_id'].nunique()
    
    print(f"   Total lineups: {total_lineups}")
    print(f"   Unique lineups: {unique_lineup_sets}")
    print(f"   Duplicates: {total_lineups - unique_lineup_sets}")
    
    if unique_lineup_sets < total_lineups:
        print("   STEP: FIX: Add diversification logic to generate unique lineups")
    
    # Issue 2: Projection accuracy
    print(f"\n ISSUE 2: PROJECTION ACCURACY")
    avg_projected = summary_df['projected_fppg'].mean()
    avg_actual = summary_df['actual_fppg'].mean()
    accuracy = (avg_actual / avg_projected * 100) if avg_projected > 0 else 0
    
    print(f"   Average projected: {avg_projected:.1f} FPPG")
    print(f"   Average actual: {avg_actual:.1f} FPPG")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    if accuracy < 70:
        print("   STEP: FIX: Projections are too optimistic - need recalibration")
        print("   STEP: FIX: Use historical average methodology instead of ML projections")
    
    # Issue 3: Player matching
    print(f"\n ISSUE 3: PLAYER MATCHING")
    avg_players_found = summary_df['players_found'].mean()
    print(f"   Average players found: {avg_players_found:.1f}/9")
    
    if avg_players_found < 8:
        print("   STEP: FIX: Improve player name matching algorithm")
        print("   STEP: FIX: Validate slate data before lineup generation")
    
    # Issue 4: Salary utilization
    print(f"\n ISSUE 4: SALARY UTILIZATION")
    avg_salary = summary_df['total_salary'].mean()
    salary_cap = 35000  # FanDuel salary cap
    utilization = (avg_salary / salary_cap * 100) if salary_cap > 0 else 0
    
    print(f"   Average salary used: ${avg_salary:,.0f}")
    print(f"   Salary cap: ${salary_cap:,.0f}")
    print(f"   Utilization: {utilization:.1f}%")
    
    if utilization < 95:
        print("   STEP: FIX: Increase salary utilization for better players")
    elif utilization > 100:
        print("   STEP: FIX: Lineup exceeds salary cap - fix optimizer")
    
    # Issue 5: Position analysis
    print(f"\n ISSUE 5: POSITION DISTRIBUTION")
    position_counts = details_df['position'].value_counts()
    print("   Position distribution:")
    for pos, count in position_counts.items():
        print(f"     {pos}: {count} selections")
    
    # Generate recommendations
    print(f"\nSTEP: RECOMMENDED FIXES:")
    print("   1. Switch to conservative historical averages")
    print("   2. Add lineup diversification algorithm")
    print("   3. Improve player name matching")
    print("   4. Validate slate data quality")
    print("   5. Recalibrate projection models")
    
    # Save diagnostic report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"../data/lineup_diagnostic_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("LINEUP DIAGNOSTIC REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"SUMMARY STATISTICS:\n")
        f.write(f"Total lineups: {total_lineups}\n")
        f.write(f"Unique lineups: {unique_lineup_sets}\n")
        f.write(f"Projection accuracy: {accuracy:.1f}%\n")
        f.write(f"Average players found: {avg_players_found:.1f}/9\n")
        f.write(f"Salary utilization: {utilization:.1f}%\n\n")
        
        f.write("CRITICAL ISSUES:\n")
        if unique_lineup_sets < total_lineups:
            f.write("- Duplicate lineups generated\n")
        if accuracy < 70:
            f.write("- Projections too optimistic\n")
        if avg_players_found < 8:
            f.write("- Poor player matching\n")
        
        f.write("\nRECOMMENDED ACTIONS:\n")
        f.write("1. Implement conservative projection methodology\n")
        f.write("2. Add lineup diversification logic\n")
        f.write("3. Fix player name matching algorithm\n")
        f.write("4. Validate input data quality\n")
    
    print(f"\nSUCCESS: Diagnostic report saved: {report_file}")

if __name__ == "__main__":
    analyze_lineup_issues()

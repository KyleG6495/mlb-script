#!/usr/bin/env python3
"""
 QUICK LINEUP VALIDATION
Validates championship lineups before FanDuel submission
"""

import pandas as pd
import glob
from datetime import datetime
import os

def check_latest_lineups():
    """Check the most recent championship lineups"""
    
    print(" LINEUP VALIDATION SYSTEM")
    print("="*50)
    
    # Find latest championship files
    championship_files = glob.glob("../data/CHAMPIONSHIP_LINEUP_*_*.csv")
    if not championship_files:
        print("ERROR: No championship lineup files found!")
        return
    
    # Get latest batch by timestamp
    latest_files = sorted(championship_files, reverse=True)[:10]
    
    print(f" Found {len(latest_files)} recent lineup files")
    print()
    
    # Load original slate to check for IL players
    try:
        original_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        il_players = set(original_slate[original_slate['Injury Indicator'] == 'IL']['Nickname'].str.lower())
        print(f"WARNING:  IL Players to avoid: {len(il_players)}")
    except:
        il_players = set()
        print("WARNING:  Could not load IL player list")
    
    lineup_summary = []
    errors_found = []
    
    for i, file_path in enumerate(latest_files, 1):
        try:
            # Extract lineup info from filename
            filename = os.path.basename(file_path)
            parts = filename.replace('.csv', '').split('_')
            
            if len(parts) >= 4:
                lineup_num = parts[2]
                strategy = parts[3] if len(parts) > 3 else "Unknown"
                timestamp = parts[-1] if len(parts) > 4 else "Unknown"
            else:
                lineup_num = str(i)
                strategy = "Unknown"
                timestamp = "Unknown"
            
            print(f"\nLINEUP: LINEUP #{lineup_num} ({strategy})")
            print("-" * 40)
            
            # Load lineup
            lineup_df = pd.read_csv(file_path)
            
            if lineup_df.empty:
                print("ERROR: Empty lineup file")
                errors_found.append(f"Lineup {lineup_num}: Empty file")
                continue
            
            # Extract player info and check salary
            total_salary = 0
            total_projection = 0
            players_found = []
            il_violations = []
            
            # Check each position
            positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
            
            for pos in positions:
                if pos in lineup_df.columns and not pd.isna(lineup_df[pos].iloc[0]):
                    player_entry = str(lineup_df[pos].iloc[0])
                    if ':' in player_entry:
                        player_id, player_name = player_entry.split(':', 1)
                        players_found.append((pos, player_name))
                        
                        # Check if player is on IL
                        if player_name.lower() in il_players:
                            il_violations.append(f"{player_name} ({pos})")
            
            # Get salary and projection from summary columns
            if 'Total_Salary' in lineup_df.columns:
                total_salary = lineup_df['Total_Salary'].iloc[0]
            if 'Total_Projection' in lineup_df.columns:
                total_projection = lineup_df['Total_Projection'].iloc[0]
            
            # Display lineup
            for pos, player in players_found:
                print(f"{pos:<4} | {player}")
            
            # Validation checks
            print(f"\nMONEY: Salary: ${total_salary:,}")
            print(f"DATA: Projection: {total_projection:.1f} FPPG")
            
            # Check for violations
            violations = []
            if total_salary > 35000:
                violations.append(f"ERROR: Over salary cap: ${total_salary:,}")
            if len(players_found) != 9:
                violations.append(f"ERROR: Wrong player count: {len(players_found)}/9")
            if il_violations:
                violations.append(f"ERROR: IL Players: {', '.join(il_violations)}")
            if total_projection < 100:
                violations.append(f"WARNING:  Low projection: {total_projection:.1f} FPPG")
            
            if violations:
                print("\n ISSUES FOUND:")
                for violation in violations:
                    print(f"   {violation}")
                errors_found.extend([f"Lineup {lineup_num}: {v}" for v in violations])
            else:
                print("\nSUCCESS: LINEUP VALIDATED - Ready for submission!")
            
            lineup_summary.append({
                'Lineup': lineup_num,
                'Strategy': strategy,
                'Salary': total_salary,
                'Projection': total_projection,
                'Players': len(players_found),
                'Status': 'READY' if not violations else 'ISSUES'
            })
            
        except Exception as e:
            print(f"ERROR: Error checking {filename}: {str(e)}")
            errors_found.append(f"Lineup {i}: File error - {str(e)}")
    
    # Final summary
    print("\n" + "="*60)
    print("DATA: LINEUP VALIDATION SUMMARY")
    print("="*60)
    
    if lineup_summary:
        summary_df = pd.DataFrame(lineup_summary)
        print(summary_df.to_string(index=False))
        
        ready_count = len(summary_df[summary_df['Status'] == 'READY'])
        print(f"\nSUCCESS: Ready for submission: {ready_count}/{len(summary_df)} lineups")
        
        if ready_count > 0:
            avg_projection = summary_df[summary_df['Status'] == 'READY']['Projection'].mean()
            print(f"DATA: Average projection: {avg_projection:.1f} FPPG")
    
    if errors_found:
        print(f"\n ERRORS FOUND ({len(errors_found)}):")
        for error in errors_found[:10]:  # Show first 10 errors
            print(f"   {error}")
        if len(errors_found) > 10:
            print(f"   ... and {len(errors_found) - 10} more errors")
    else:
        print("\nCOMPLETE: NO ERRORS FOUND - All lineups look good!")
    
    print("\nSTART: READY TO UPLOAD TO FANDUEL!")

if __name__ == "__main__":
    check_latest_lineups()

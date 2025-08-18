#!/usr/bin/env python3
"""
analyze_sportsbook_props.py

Analyze what prop types are available across all sportsbooks to understand
what models we need to train.
"""
import pandas as pd
import os

def analyze_props():
    print(" ANALYZING SPORTSBOOK PROP TYPES")
    print("="*60)
    
    # FanDuel
    try:
        fd_file = "../fd_current_slate/fd_slate_today.csv"
        if os.path.exists(fd_file):
            df_fd = pd.read_csv(fd_file)
            print(f"DATA: FanDuel: {len(df_fd)} total props")
            if 'variable' in df_fd.columns:
                fd_props = df_fd['variable'].value_counts()
                print("Top FanDuel prop types:")
                print(fd_props.head(10))
            print()
    except Exception as e:
        print(f"ERROR: Error loading FanDuel: {e}")
    
    # PrizePicks
    try:
        pp_files = [f for f in os.listdir("../data") if f.startswith('PP_mlb_picks_') and f.endswith('.xlsx')]
        if pp_files:
            pp_file = max(pp_files, key=lambda x: x)  # Get most recent
            df_pp = pd.read_excel(f"../data/{pp_file}")
            print(f"DATA: PrizePicks ({pp_file}): {len(df_pp)} players")
            
            # Count prop types (columns other than player_name)
            prop_cols = [col for col in df_pp.columns if col != 'player_name']
            prop_counts = {}
            for col in prop_cols:
                prop_counts[col] = df_pp[col].notna().sum()
            
            # Sort by frequency
            sorted_props = sorted(prop_counts.items(), key=lambda x: x[1], reverse=True)
            print("PrizePicks prop types by frequency:")
            for prop, count in sorted_props[:15]:
                print(f"  {prop}: {count}")
            print()
    except Exception as e:
        print(f"ERROR: Error loading PrizePicks: {e}")
    
    # Underdog Fantasy
    try:
        ud_files = [f for f in os.listdir("../data") if f.startswith('today_pitcher_props_') and f.endswith('.csv')]
        if ud_files:
            ud_file = max(ud_files, key=lambda x: x)  # Get most recent
            df_ud = pd.read_csv(f"../data/{ud_file}")
            print(f"DATA: Underdog ({ud_file}): {len(df_ud)} props")
            if 'stat_type' in df_ud.columns:
                ud_props = df_ud['stat_type'].value_counts()
                print("Top Underdog prop types:")
                print(ud_props.head(15))
            print()
    except Exception as e:
        print(f"ERROR: Error loading Underdog: {e}")
    
    # Combined analysis
    print("TARGET: RECOMMENDED MODELS TO TRAIN")
    print("="*40)
    print("HITTER MODELS (current SUCCESS:):")
    print("  SUCCESS: hits - Available across all books")
    print("  SUCCESS: total_bases - Available across all books") 
    print("  SUCCESS: runs - Available across all books")
    print("  SUCCESS: rbi - Available across all books")
    print("  SUCCESS: home_runs - Available across all books")
    print("  SUCCESS: hitter_strikeouts - NEW model trained!")
    print()
    print("PITCHER MODELS (needed):")
    print("  SWAP: pitcher_strikeouts - Existing model, map correctly")
    print("   outs/innings - May need new model")
    print("   walks - Consider adding")
    print("   hits_allowed - Consider adding")
    print()
    print("POTENTIAL NEW MODELS:")
    print("   stolen_bases - Available in some books")
    print("   doubles - Available in some books")
    print("   fantasy_points - Available in some books")

if __name__ == "__main__":
    analyze_props()

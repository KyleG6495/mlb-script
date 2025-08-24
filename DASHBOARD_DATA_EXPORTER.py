#!/usr/bin/env python3
"""
DASHBOARD DATA EXPORTER
Exports all dashboard data to copy-friendly text files
"""

import pandas as pd
import os
from datetime import datetime
from file_finder_utils import get_data_files, safe_read_csv

def export_dashboard_data():
    """Export all dashboard data to text files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = "../exports"
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    print("🔄 EXPORTING DASHBOARD DATA...")
    print("=" * 50)
    
    # Get data files
    data_files = get_data_files()
    
    # 1. Export Elite Lineups
    if 'elite_lineups' in data_files:
        print("📊 Exporting Elite Lineups...")
        df = safe_read_csv(data_files['elite_lineups'])
        if df is not None:
            export_file = os.path.join(export_dir, f"elite_lineups_export_{timestamp}.txt")
            with open(export_file, 'w') as f:
                f.write("🏆 ELITE TOURNAMENT LINEUPS\n")
                f.write("=" * 50 + "\n\n")
                
                for i, row in df.iterrows():
                    f.write(f"Lineup #{i+1}:\n")
                    f.write(f"  Stack Type: {row.get('stack_team', 'Unknown')}\n")
                    f.write(f"  Salary: ${row.get('total_salary', 0):,}\n")
                    f.write(f"  Projection: {row.get('total_projection', 0):.1f}\n")
                    f.write(f"  Ownership: {row.get('avg_ownership', 0):.1%}\n")
                    f.write(f"  Tournament Score: {row.get('tournament_score', 0):.1f}\n")
                    
                    # List players if available
                    if 'players' in row and pd.notna(row['players']):
                        try:
                            import ast
                            players = ast.literal_eval(str(row['players']))
                            f.write("  Players:\n")
                            for player in players:
                                f.write(f"    {player.get('Nickname', 'Unknown')} ({player.get('Position', '?')}) - "
                                       f"${player.get('Salary', 0)} | {player.get('enhanced_fppg', 0):.1f} proj\n")
                        except:
                            pass
                    
                    f.write("\n")
            print(f"  ✅ Saved to: {export_file}")
    
    # 2. Export Ownership Data
    if 'ownership' in data_files:
        print("📈 Exporting Ownership Analysis...")
        df = safe_read_csv(data_files['ownership'])
        if df is not None:
            export_file = os.path.join(export_dir, f"ownership_analysis_{timestamp}.txt")
            with open(export_file, 'w') as f:
                f.write("📈 OWNERSHIP ANALYSIS\n")
                f.write("=" * 50 + "\n\n")
                
                # Chalk plays (>25% owned)
                chalk = df[df['ownership'] > 0.25].sort_values('ownership', ascending=False)
                f.write("🔥 CHALK PLAYS (>25% ownership):\n")
                for _, player in chalk.head(10).iterrows():
                    f.write(f"  {player['player_name']} - {player['ownership']:.1%} owned\n")
                f.write("\n")
                
                # Contrarian plays (<8% owned)
                contrarian = df[df['ownership'] < 0.08].sort_values('leverage_score', ascending=False)
                f.write("🎯 CONTRARIAN PLAYS (<8% ownership):\n")
                for _, player in contrarian.head(15).iterrows():
                    f.write(f"  {player['player_name']} - {player['ownership']:.1%} owned | "
                           f"Leverage: {player['leverage_score']:.2f}\n")
                f.write("\n")
                
                # High leverage plays
                leverage = df.sort_values('leverage_score', ascending=False)
                f.write("⚡ HIGH LEVERAGE PLAYS:\n")
                for _, player in leverage.head(15).iterrows():
                    f.write(f"  {player['player_name']} - {player['ownership']:.1%} owned | "
                           f"Leverage: {player['leverage_score']:.2f}\n")
            print(f"  ✅ Saved to: {export_file}")
    
    # 3. Export Current Slate Overview
    if 'slate' in data_files:
        print("🎯 Exporting Slate Overview...")
        df = safe_read_csv(data_files['slate'])
        if df is not None:
            # Filter to active players only
            if 'Injury Indicator' in df.columns:
                active_df = df[df['Injury Indicator'].isna()]
            else:
                active_df = df
                
            export_file = os.path.join(export_dir, f"slate_overview_{timestamp}.txt")
            with open(export_file, 'w') as f:
                f.write("🎯 TODAY'S SLATE OVERVIEW\n")
                f.write("=" * 50 + "\n\n")
                
                # Probable pitchers
                pitchers = active_df[
                    (active_df['Position'] == 'P') & 
                    (active_df.get('Probable Pitcher', '') == 'Yes')
                ].sort_values('FPPG', ascending=False)
                
                f.write("⚾ PROBABLE PITCHERS:\n")
                for _, pitcher in pitchers.iterrows():
                    f.write(f"  {pitcher['Nickname']} ({pitcher['Team']}) - "
                           f"${pitcher['Salary']} | {pitcher['FPPG']:.1f} proj | "
                           f"vs {pitcher['Opponent']}\n")
                f.write("\n")
                
                # Top hitters by projection
                hitters = active_df[
                    (active_df['Position'] != 'P') & 
                    (active_df.get('Batting Order', 0) > 0)
                ].sort_values('FPPG', ascending=False)
                
                f.write("🏏 TOP PROJECTED HITTERS:\n")
                for _, hitter in hitters.head(20).iterrows():
                    f.write(f"  {hitter['Nickname']} ({hitter['Position']}, {hitter['Team']}) - "
                           f"${hitter['Salary']} | {hitter['FPPG']:.1f} proj\n")
                f.write("\n")
                
                # Games summary
                games = active_df['Game'].unique()
                f.write("🎮 GAMES TODAY:\n")
                for game in sorted(games):
                    f.write(f"  {game}\n")
                    
            print(f"  ✅ Saved to: {export_file}")
    
    print(f"\n✅ EXPORT COMPLETE!")
    print(f"📁 Files saved to: {export_dir}/")
    print(f"📋 You can now copy/paste from these text files!")

if __name__ == "__main__":
    export_dashboard_data()

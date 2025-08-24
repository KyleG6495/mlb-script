#!/usr/bin/env python3
"""
Simple Export Tool - Export any lineup directly without web interface
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

def export_specific_lineup(lineup_id=0):
    """Export a specific lineup by ID"""
    print(f"🚀 EXPORTING LINEUP #{lineup_id + 1}")
    print("=" * 50)
    
    # Define paths
    fd_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate')
    
    # Find the latest Enhanced_Lineups file
    enhanced_files = list(fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
    if not enhanced_files:
        print("❌ ERROR: No Enhanced_Lineups_FD_Format files found")
        return None
    
    latest_file = max(enhanced_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Using file: {latest_file.name}")
    
    try:
        # Load the lineup data
        df = pd.read_csv(latest_file)
        print(f"📊 Available lineups: {len(df)}")
        
        if lineup_id >= len(df):
            print(f"❌ ERROR: Lineup #{lineup_id + 1} not found (max: {len(df)})")
            return None
        
        # Get the specific lineup
        lineup_row = df.iloc[lineup_id]
        
        print(f"📋 Lineup #{lineup_id + 1} Details:")
        print(f"   💰 Salary: ${lineup_row.get('Total_Salary', 'N/A'):,}")
        print(f"   📈 Projection: {lineup_row.get('Total_Projection', 'N/A')}")
        print(f"   🏆 Contest: {lineup_row.get('Contest_Type', 'N/A')}")
        
        # Show the lineup
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        print(f"\n👥 Players:")
        for pos in positions:
            if pos in lineup_row:
                value = str(lineup_row[pos])
                if ':' in value:
                    player_id, player_name = value.split(':', 1)
                    print(f"   {pos:4}: {player_name}")
                else:
                    print(f"   {pos:4}: {value}")
        
        # Create single lineup export
        export_df = pd.DataFrame([lineup_row])
        
        # Generate export filename - FanDuel ready format
        export_filename = f"FD_READY_Lineup_{lineup_id + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_path = fd_path / export_filename
        
        # Export with only the essential FanDuel columns
        essential_columns = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        available_columns = [col for col in essential_columns if col in export_df.columns]
        
        final_df = export_df[available_columns]
        final_df.to_csv(export_path, index=False)
        
        print(f"\n✅ SUCCESS: Exported to {export_filename}")
        print(f"📁 Full path: {export_path}")
        print(f"📋 Ready for FanDuel upload!")
        
        return str(export_path)
        
    except Exception as e:
        print(f"❌ ERROR during export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def export_all_lineups():
    """Export all lineups at once"""
    print(f"🚀 EXPORTING ALL LINEUPS")
    print("=" * 50)
    
    # Define paths
    fd_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate')
    
    # Find the latest Enhanced_Lineups file
    enhanced_files = list(fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
    if not enhanced_files:
        print("❌ ERROR: No Enhanced_Lineups_FD_Format files found")
        return None
    
    latest_file = max(enhanced_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Using file: {latest_file.name}")
    
    try:
        # Load all lineups
        df = pd.read_csv(latest_file)
        print(f"📊 Total lineups: {len(df)}")
        
        # Export all lineups
        essential_columns = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        available_columns = [col for col in essential_columns if col in df.columns]
        
        final_df = df[available_columns]
        
        # Generate bulk export filename
        bulk_filename = f"FD_READY_ALL_{len(df)}_LINEUPS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        bulk_path = fd_path / bulk_filename
        
        final_df.to_csv(bulk_path, index=False)
        
        print(f"\n✅ SUCCESS: Exported all {len(df)} lineups to {bulk_filename}")
        print(f"📁 Full path: {bulk_path}")
        print(f"📋 Ready for FanDuel bulk upload!")
        
        return str(bulk_path)
        
    except Exception as e:
        print(f"❌ ERROR during bulk export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_player_team(player_string):
    """Extract team from player string"""
    if ':' in player_string:
        return player_string.split(':')[1].strip()
    return str(player_string)

def find_stack_lineups(team_name):
    """Find lineups that contain a stack from the specified team"""
    print(f"🔍 SEARCHING FOR {team_name.upper()} STACK LINEUPS")
    print("=" * 50)
    
    # Define paths
    fd_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate')
    
    # Find the latest Enhanced_Lineups file
    enhanced_files = list(fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
    if not enhanced_files:
        print("❌ ERROR: No Enhanced_Lineups_FD_Format files found")
        return []
    
    latest_file = max(enhanced_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Using file: {latest_file.name}")
    
    try:
        df = pd.read_csv(latest_file)
        
        # Load team data to map players to teams
        team_file = fd_path / "fd_slate_today.csv"
        if team_file.exists():
            team_df = pd.read_csv(team_file)
            # Create a mapping of player names to teams
            player_team_map = {}
            for _, player in team_df.iterrows():
                player_name = player.get('Nickname', player.get('Name', ''))
                team = player.get('Team', '')
                if player_name and team:
                    player_team_map[player_name.lower()] = team.upper()
        else:
            player_team_map = {}
        
        stack_lineups = []
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        
        for idx, row in df.iterrows():
            team_count = {}
            lineup_players = []
            
            for pos in positions:
                if pos in row:
                    player_string = str(row[pos])
                    if ':' in player_string:
                        player_name = player_string.split(':')[1].strip()
                        lineup_players.append(f"{pos}: {player_name}")
                        
                        # Try to find team from mapping
                        player_lower = player_name.lower()
                        found_team = None
                        
                        for mapped_name, mapped_team in player_team_map.items():
                            if mapped_name in player_lower or player_lower in mapped_name:
                                found_team = mapped_team
                                break
                        
                        if found_team:
                            team_count[found_team] = team_count.get(found_team, 0) + 1
                        else:
                            # Fallback: common team abbreviations in names
                            name_upper = player_name.upper()
                            if any(team_abbr in name_upper for team_abbr in ['NYY', 'BOS', 'LAD', 'HOU', 'ATL']):
                                for team_abbr in ['NYY', 'BOS', 'LAD', 'HOU', 'ATL']:
                                    if team_abbr in name_upper:
                                        team_count[team_abbr] = team_count.get(team_abbr, 0) + 1
                                        break
            
            # Check if this lineup has a stack from the requested team
            target_team = team_name.upper()
            team_players = team_count.get(target_team, 0)
            
            if team_players >= 2:  # Consider 2+ players a "stack"
                stack_lineups.append({
                    'index': idx,
                    'lineup_num': idx + 1,
                    'team_players': team_players,
                    'salary': row.get('Total_Salary', 'N/A'),
                    'projection': row.get('Total_Projection', 'N/A'),
                    'contest': row.get('Contest_Type', 'N/A'),
                    'players': lineup_players,
                    'all_teams': team_count
                })
        
        if stack_lineups:
            print(f"🎯 Found {len(stack_lineups)} lineups with {target_team} stacks:")
            print()
            
            for lineup in stack_lineups:
                print(f"Lineup #{lineup['lineup_num']:2}: ${lineup['salary']:5,} | {lineup['projection']:5.1f} proj | {lineup['contest']} | {lineup['team_players']} {target_team} players")
                
                # Show team breakdown
                team_summary = []
                for team, count in lineup['all_teams'].items():
                    if count > 1:
                        team_summary.append(f"{team}({count})")
                if team_summary:
                    print(f"             Teams: {', '.join(team_summary)}")
                print()
        else:
            print(f"❌ No lineups found with {target_team} stacks")
            print("Available teams in lineups:")
            # Show all teams found
            all_teams = set()
            for idx, row in df.iterrows():
                for pos in positions:
                    if pos in row:
                        player_string = str(row[pos])
                        if ':' in player_string:
                            player_name = player_string.split(':')[1].strip()
                            for mapped_name, mapped_team in player_team_map.items():
                                if mapped_name in player_name.lower():
                                    all_teams.add(mapped_team)
                                    break
            if all_teams:
                print(f"   {', '.join(sorted(all_teams))}")
        
        return stack_lineups
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def list_available_lineups():
    """Show all available lineups"""
    print(f"📋 AVAILABLE LINEUPS")
    print("=" * 50)
    
    # Define paths
    fd_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate')
    
    # Find the latest Enhanced_Lineups file
    enhanced_files = list(fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
    if not enhanced_files:
        print("❌ ERROR: No Enhanced_Lineups_FD_Format files found")
        return
    
    latest_file = max(enhanced_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Using file: {latest_file.name}")
    
    try:
        df = pd.read_csv(latest_file)
        print(f"📊 Total lineups: {len(df)}")
        print()
        
        for idx, row in df.iterrows():
            print(f"Lineup #{idx + 1:2}: ${row.get('Total_Salary', 'N/A'):5,} | {row.get('Total_Projection', 'N/A'):5.1f} proj | {row.get('Contest_Type', 'N/A')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("🎯 SIMPLE LINEUP EXPORTER")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            export_all_lineups()
        elif sys.argv[1] == "list":
            list_available_lineups()
        elif sys.argv[1] == "stack" and len(sys.argv) > 2:
            # Search for stack lineups
            team = sys.argv[2]
            stack_lineups = find_stack_lineups(team)
            if stack_lineups and len(sys.argv) > 3:
                # Export specific stack lineup
                try:
                    choice = int(sys.argv[3]) - 1
                    if 0 <= choice < len(stack_lineups):
                        lineup_idx = stack_lineups[choice]['index']
                        export_specific_lineup(lineup_idx)
                    else:
                        print(f"❌ Invalid choice. Pick 1-{len(stack_lineups)}")
                except ValueError:
                    print("❌ Invalid lineup number")
        else:
            try:
                lineup_id = int(sys.argv[1]) - 1  # Convert to 0-based index
                export_specific_lineup(lineup_id)
            except ValueError:
                print("❌ Invalid lineup number")
    else:
        print("Usage:")
        print("  python simple_export.py 1              # Export lineup #1")
        print("  python simple_export.py 5              # Export lineup #5") 
        print("  python simple_export.py all            # Export all lineups")
        print("  python simple_export.py list           # List all lineups")
        print("  python simple_export.py stack NYY      # Find NYY stack lineups")
        print("  python simple_export.py stack LAD      # Find LAD stack lineups")
        print("  python simple_export.py stack NYY 1    # Export 1st NYY stack lineup")
        print()
        list_available_lineups()

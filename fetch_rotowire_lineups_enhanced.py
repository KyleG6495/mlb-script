#!/usr/bin/env python3
"""
ROTOWIRE LINEUP FETCHER - ENHANCED VERSION
==========================================
Fetch expected and confirmed lineups from Rotowire to enhance DFS projections.
This will update the fd_slate_today.csv with batting order information.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
import re
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_rotowire_lineups():
    """Fetch MLB lineups from Rotowire with enhanced coverage for expected and confirmed lineups"""
    
    print("FETCHING ROTOWIRE LINEUPS - ENHANCED VERSION")
    print("=" * 55)
    
    # Rotowire MLB lineups URL
    url = "https://www.rotowire.com/baseball/daily-lineups.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    lineup_data = {}
    pitcher_data = {}
    
    try:
        print("Fetching lineup data from Rotowire...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("Searching for ALL game containers (expected and confirmed lineups)...")
        
        # Load today's FD slate to filter only relevant teams
        fd_slate_teams = set()
        try:
            import pandas as pd
            slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
            fd_slate_teams = set(slate_df['Team'].unique())
            print(f"FD slate teams: {sorted(fd_slate_teams)}")
        except:
            # Fallback to all MLB teams if slate file not available
            fd_slate_teams = {'ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CIN', 'CLE', 'COL', 'CWS', 'KC', 'LAA', 'LAD', 'MIL', 'SD', 'SF', 'TEX'}
        
        # Find all game containers using the correct Rotowire classes
        game_containers = soup.find_all('div', class_='lineup__box')
        print(f"Found {len(game_containers)} total game containers")
        
        team_lineups = {}
        processed_games = 0
        
        # Process ALL game containers to capture both expected and confirmed lineups
        for container_idx, container in enumerate(game_containers):
            try:
                # Extract teams from logos/abbreviations
                team_abbr_elements = container.find_all('div', class_='lineup__abbr')
                
                teams_in_game = []
                for abbr_elem in team_abbr_elements:
                    team_abbr = abbr_elem.get_text().strip()
                    # Handle both 2 and 3 character team abbreviations
                    if len(team_abbr) >= 2 and len(team_abbr) <= 3 and team_abbr.isalpha():
                        teams_in_game.append(team_abbr)
                
                # Debug: print all containers
                if len(teams_in_game) >= 2:
                    away_team = teams_in_game[0]
                    home_team = teams_in_game[1]
                    print(f"Container {container_idx + 1}: Found {away_team} @ {home_team}")
                else:
                    print(f"Container {container_idx + 1}: Could not extract teams (found {len(teams_in_game)} teams)")
                    continue
                
                # Only process if we found teams and they're in FD slate
                if len(teams_in_game) >= 2:
                    # Skip games where neither team is in today's FD slate
                    if away_team not in fd_slate_teams and home_team not in fd_slate_teams:
                        print(f"  -> Skipping {away_team} @ {home_team} - not in FD slate")
                        continue
                    
                    print(f"  -> Processing {away_team} @ {home_team} - IN FD SLATE")
                    processed_games += 1
                    
                    # Find all lineup lists in this container
                    lineup_lists = container.find_all('ul', class_='lineup__list')
                    print(f"  -> Found {len(lineup_lists)} lineup lists")
                    
                    if len(lineup_lists) >= 2:
                        # First lineup list is visiting team, second is home team
                        team_list_pairs = [
                            (away_team, lineup_lists[0]),  # Visiting team gets first list
                            (home_team, lineup_lists[1])   # Home team gets second list
                        ]
                        
                        for current_team, lineup_list in team_list_pairs:
                            # Skip if this team is not in FD slate
                            if current_team not in fd_slate_teams:
                                print(f"    -> Skipping {current_team} - not in FD slate")
                                continue
                            
                            print(f"    -> Processing {current_team} lineup")
                            
                            if current_team not in team_lineups:
                                team_lineups[current_team] = []
                            
                            player_elements = lineup_list.find_all('li', class_='lineup__player')
                            
                            for j, player_element in enumerate(player_elements[:9]):
                                try:
                                    # Extract position
                                    pos_div = player_element.find('div', class_='lineup__pos')
                                    if not pos_div:
                                        continue
                                    
                                    position = pos_div.get_text().strip()
                                    if position not in ['1B', '2B', '3B', 'SS', 'C', 'RF', 'CF', 'LF', 'DH']:
                                        continue
                                    
                                    # Extract player name from text content
                                    full_text = player_element.get_text().strip()
                                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                                    
                                    # Player name should be the second line (after position)
                                    player_name = None
                                    if len(lines) >= 2:
                                        player_name = lines[1].strip()
                                    
                                    if player_name and len(player_name) > 2:
                                        # Clean the player name
                                        player_name = re.sub(r'[^\w\s.]', ' ', player_name).strip()
                                        player_name = ' '.join(player_name.split())
                                        
                                        if len(player_name) > 3 and len(player_name.split()) >= 2:
                                            team_lineups[current_team].append({
                                                'position': position,
                                                'player': player_name,
                                                'order': len(team_lineups[current_team]) + 1
                                            })
                                            
                                            print(f"      {current_team} - {position} {player_name}")
                                
                                except Exception as e:
                                    continue
                    
                    else:
                        print(f"  -> Warning: Only found {len(lineup_lists)} lineup lists for {away_team} @ {home_team}")
                
            except Exception as e:
                print(f"  -> Error processing container {container_idx + 1}: {e}")
                continue
        
        print(f"\nProcessed {processed_games} games from {len(game_containers)} containers")
        
        # Convert team lineups to our format
        total_players = 0
        
        # First, deduplicate and limit to 9 players per team
        cleaned_team_lineups = {}
        for team, players in team_lineups.items():
            # Remove duplicates by player name
            seen_players = set()
            unique_players = []
            for player_info in players:
                player_name = player_info['player']
                if player_name not in seen_players:
                    seen_players.add(player_name)
                    unique_players.append(player_info)
                if len(unique_players) >= 9:  # Limit to 9 players per team
                    break
            
            if unique_players:
                cleaned_team_lineups[team] = unique_players
                print(f"\n{team} lineup ({len(unique_players)} players):")
                for i, player_info in enumerate(unique_players, 1):
                    lineup_key = f"{team}_{player_info['player']}"
                    lineup_data[lineup_key] = i
                    total_players += 1
                    print(f"  {i}. {player_info['position']} {player_info['player']}")
        
        print(f"\nSuccessfully parsed {total_players} player batting orders from {len(cleaned_team_lineups)} teams")
        
        # Extract starting pitchers with cleaner parsing
        print(f"\nExtracting starting pitchers...")
        
        full_text = soup.get_text()
        
        # Look for cleaner pitcher patterns
        pitcher_patterns = [
            r'([A-Za-z.\s]{3,25})\s+([LR])\s+(\d+-\d+)\s+(\d+\.\d+)\s+ERA',
        ]
        
        pitcher_count = 0
        for pattern in pitcher_patterns:
            pitcher_matches = re.findall(pattern, full_text)
            for match in pitcher_matches:
                if len(match) >= 4:
                    pitcher_name = match[0].strip()
                    handedness = match[1]
                    record = match[2]
                    era = match[3]
                    
                    # Clean pitcher name
                    pitcher_name = re.sub(r'[^\w\s.]', '', pitcher_name).strip()
                    
                    # Validate pitcher name
                    if (len(pitcher_name) > 3 and 
                        len(pitcher_name) < 30 and
                        not any(char.isdigit() for char in pitcher_name) and
                        len(pitcher_name.split()) >= 2 and  # First and last name
                        not any(word.lower() in ['confirmed', 'lineup', 'intel', 'odds', 'home', 'run', 'era'] for word in pitcher_name.split())):
                        
                        try:
                            pitcher_data[pitcher_name] = {
                                'handedness': handedness,
                                'record': record,
                                'era': float(era)
                            }
                            pitcher_count += 1
                        except ValueError:
                            pass
        
        print(f"Found {pitcher_count} starting pitchers")
        
        # Save data to temp files
        try:
            print(f"DEBUG: lineup_data has {len(lineup_data)} items")
            print(f"DEBUG: pitcher_data has {len(pitcher_data)} items")
            
            if lineup_data:
                print("DEBUG: Saving lineup data...")
                with open('temp_lineup_data.json', 'w') as f:
                    json.dump(lineup_data, f, indent=2)
                print(f"\nSaved {len(lineup_data)} batting order assignments to temp_lineup_data.json")
            else:
                print("DEBUG: No lineup data to save")
            
            if pitcher_data:
                print("DEBUG: Saving pitcher data...")
                with open('temp_pitcher_data.json', 'w') as f:
                    json.dump(pitcher_data, f, indent=2)
                print(f"Saved {len(pitcher_data)} starting pitcher records to temp_pitcher_data.json")
            else:
                print("DEBUG: No pitcher data to save")
        except Exception as e:
            print(f"Error saving data files: {e}")
            import traceback
            traceback.print_exc()
        
        # Coverage summary
        teams_covered = set(cleaned_team_lineups.keys())
        fd_teams_covered = teams_covered & fd_slate_teams
        missing_teams = fd_slate_teams - teams_covered
        
        print(f"\n" + "=" * 55)
        print(f"COVERAGE SUMMARY:")
        print(f"Teams in FD slate: {len(fd_slate_teams)}")
        print(f"Teams with lineups: {len(fd_teams_covered)}")
        print(f"Coverage: {len(fd_teams_covered)}/{len(fd_slate_teams)} = {len(fd_teams_covered)/len(fd_slate_teams)*100:.1f}%")
        print(f"Teams covered: {sorted(fd_teams_covered)}")
        if missing_teams:
            print(f"Teams missing: {sorted(missing_teams)}")
        print(f"=" * 55)
        
        return len(lineup_data) > 0 or len(pitcher_data) > 0
        
    except requests.RequestException as e:
        print(f"Error fetching Rotowire data: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def apply_batting_orders():
    """Apply the extracted batting orders to the FD slate"""
    
    print("\n" + "=" * 50)
    print("APPLYING BATTING ORDERS TO FD SLATE")
    print("=" * 50)
    
    try:
        # Load the lineup data
        if not os.path.exists('temp_lineup_data.json'):
            print("No lineup data file found. Run fetch_rotowire_lineups() first.")
            return False
        
        with open('temp_lineup_data.json', 'r') as f:
            lineup_data = json.load(f)
        
        print(f"Loaded {len(lineup_data)} batting order assignments")
        
        # Load the FD slate
        slate_path = "../fd_current_slate/fd_slate_today.csv"
        df = pd.read_csv(slate_path)
        print(f"Loaded FD slate with {len(df)} players")
        
        # Apply batting orders
        orders_applied = 0
        
        for index, row in df.iterrows():
            team = row['Team']
            first_name = str(row['First Name']).strip()
            last_name = str(row['Last Name']).strip()
            
            # Try different name combinations
            name_variations = [
                f"{first_name} {last_name}",
                f"{first_name.split()[0]} {last_name}" if ' ' in first_name else f"{first_name} {last_name}",
                f"{first_name[0]}. {last_name}",
                last_name
            ]
            
            batting_order = 0
            for name_var in name_variations:
                lookup_key = f"{team}_{name_var}"
                if lookup_key in lineup_data:
                    batting_order = lineup_data[lookup_key]
                    orders_applied += 1
                    break
            
            df.at[index, 'Batting Order'] = batting_order
        
        # Save the updated slate
        df.to_csv(slate_path, index=False)
        print(f"Applied {orders_applied} batting orders to FD slate")
        print(f"Updated file saved: {slate_path}")
        
        return True
        
    except Exception as e:
        print(f"Error applying batting orders: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Rotowire lineup extraction...")
    success = fetch_rotowire_lineups()
    
    if success:
        print("\nApplying batting orders to FD slate...")
        apply_batting_orders()
    else:
        print("Failed to fetch lineup data.")

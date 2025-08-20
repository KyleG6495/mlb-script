#!/usr/bin/env python3
"""
ROTOWIRE LINEUP FETCHER
=======================
Fetch expected lineups and batting orders from Rotowire to enhance DFS projections.
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
    """Fetch MLB lineups from Rotowire with improved team identification"""
    
    print("FETCHING ROTOWIRE LINEUPS")
    print("=" * 50)
    
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
        
        # Different approach: Find game containers first, then extract lineups
        print("Searching for game containers with team information...")
        
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
        
        print(f"Found {len(game_containers)} potential game containers")
        
        team_lineups = {}
        processed_games = 0
        
        # Process ALL game containers, not just the first few
        for container_idx, container in enumerate(game_containers):
            try:
                # Extract teams from logos/abbreviations
                team_abbr_elements = container.find_all('div', class_='lineup__abbr')
                
                teams_in_game = []
                for abbr_elem in team_abbr_elements:
                    team_abbr = abbr_elem.get_text().strip()
                    if len(team_abbr) == 3 and team_abbr.isalpha():
                        teams_in_game.append(team_abbr)
                
                # Only process if we found teams and they're in FD slate
                if len(teams_in_game) >= 2:
                    away_team = teams_in_game[0]
                    home_team = teams_in_game[1]
                    
                    # Skip games where neither team is in today's FD slate
                    if away_team not in fd_slate_teams and home_team not in fd_slate_teams:
                        print(f"Skipping {away_team} @ {home_team} - not in FD slate")
                        continue
                    
                    print(f"\nProcessing game {container_idx + 1}: {away_team} @ {home_team}")
                    processed_games += 1
                    
                    # Find all lineup lists in this container
                    lineup_lists = container.find_all('ul', class_='lineup__list')
                    
                    if len(lineup_lists) >= 2:
                        # First lineup list is visiting team, second is home team
                        team_list_pairs = [
                            (away_team, lineup_lists[0]),  # Visiting team gets first list
                            (home_team, lineup_lists[1])   # Home team gets second list
                        ]
                        
                        for current_team, lineup_list in team_list_pairs:
                            # Skip if this team is not in FD slate
                            if current_team not in fd_slate_teams:
                                print(f"  Skipping {current_team} - not in FD slate")
                                continue
                            
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
                                            
                                            print(f"  {current_team} - {position} {player_name}")
                                
                                except Exception as e:
                                    continue
                    
                    else:
                        print(f"  Warning: Only found {len(lineup_lists)} lineup lists for {away_team} @ {home_team}")
                
            except Exception as e:
                print(f"  Error processing container {container_idx + 1}: {e}")
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
        
        return len(lineup_data) > 0 or len(pitcher_data) > 0
        
    except requests.RequestException as e:
        print(f"Error fetching Rotowire data: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_slate_with_lineups():
    """Update the FanDuel slate with batting order information"""
    
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    
    try:
        # Load current slate
        df = pd.read_csv(slate_file)
        print(f"Loaded slate with {len(df)} players")
        
        # Try to load real lineup data
        real_lineup_data = {}
        try:
            import json
            with open('temp_lineup_data.json', 'r') as f:
                real_lineup_data = json.load(f)
            print(f"Loaded {len(real_lineup_data)} real batting orders from Rotowire")
        except:
            print("No real lineup data available, using salary-based estimates")
        
        # Filter to only teams that are in today's slate
        slate_teams = set(df['Team'].unique())
        print(f"Teams in today's slate: {sorted(slate_teams)}")
        
        hitters = df[df['Position'] != 'P'].copy()
        updated_count = 0
        real_orders_count = 0
        
        # Group by team and assign batting orders
        for team in hitters['Team'].unique():
            team_players = hitters[hitters['Team'] == team].copy()
            
            print(f"\nProcessing {team} - {len(team_players)} hitters")
            
            # First, try to use real lineup data
            team_real_orders = {}
            for key, batting_order in real_lineup_data.items():
                if key.startswith(f"{team}_"):
                    player_name = key.replace(f"{team}_", "")
                    team_real_orders[player_name] = batting_order
            
            real_matches = 0
            if team_real_orders:
                print(f"  Found {len(team_real_orders)} confirmed batting orders for {team}")
                
                # Match players by name similarity
                for idx, player in team_players.iterrows():
                    player_full_name = f"{player['First Name']} {player['Nickname']}"
                    
                    # Try exact match first
                    best_match = None
                    best_order = None
                    
                    for rotowire_name, order in team_real_orders.items():
                        if rotowire_name.lower() in player_full_name.lower() or player_full_name.lower() in rotowire_name.lower():
                            best_match = rotowire_name
                            best_order = order
                            break
                    
                    if best_match and pd.isna(df.loc[idx, 'Batting Order']):
                        df.loc[idx, 'Batting Order'] = best_order
                        updated_count += 1
                        real_orders_count += 1
                        real_matches += 1
                        print(f"    Matched: {player_full_name} -> {best_match} (Order: {best_order})")
            
            # For ALL remaining players (whether we found real data or not), use salary-based estimates
            team_indices = team_players.index
            unassigned_indices = [idx for idx in team_indices if pd.isna(df.loc[idx, 'Batting Order'])]
            
            if len(unassigned_indices) > 0:
                print(f"  Assigning salary-based orders for {len(unassigned_indices)} remaining players")
                
                # Get unassigned players and sort by salary descending
                unassigned_players = df.loc[unassigned_indices].sort_values('Salary', ascending=False)
                
                # Determine which batting orders are already used for this team
                used_orders = set(df[df['Team'] == team]['Batting Order'].dropna().astype(int))
                available_orders = [i for i in range(1, 10) if i not in used_orders]
                
                # If we need more orders than available (1-9), cycle through them
                if len(unassigned_indices) > len(available_orders):
                    # Add additional cycles of 1-9 as needed
                    additional_cycles = (len(unassigned_indices) - len(available_orders)) // 9 + 1
                    for cycle in range(additional_cycles):
                        for order in range(1, 10):
                            if order not in used_orders:
                                available_orders.append(order)
                
                # Assign orders to remaining players
                for i, (idx, player) in enumerate(unassigned_players.iterrows()):
                    if i < len(available_orders):
                        order = available_orders[i]
                        df.loc[idx, 'Batting Order'] = order
                        updated_count += 1
                        print(f"    Salary-based: {player['First Name']} {player['Nickname']} -> Order {order} (${player['Salary']})")
            
            print(f"  ✅ {team}: {real_matches} real orders + {len(unassigned_indices) - real_matches} estimated orders")
        
        # Save updated slate
        df.to_csv(slate_file, index=False)
        print(f"\nUpdated {updated_count} players with batting orders")
        print(f"Real confirmed orders: {real_orders_count}")
        print(f"Salary-based estimates: {updated_count - real_orders_count}")
        print(f"Saved updated slate to {slate_file}")
        
        # Clean up temp file
        try:
            import os
            if os.path.exists('temp_lineup_data.json'):
                os.remove('temp_lineup_data.json')
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"Error updating slate: {e}")
        return False

def main():
    """Main function to fetch and update lineups"""
    
    print(f"Starting lineup fetch at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try to fetch from Rotowire
    success = fetch_rotowire_lineups()
    
    if not success:
        print("WARNING: Rotowire fetch failed, using estimated batting orders")
    
    # Update slate with batting order information
    update_success = update_slate_with_lineups()
    
    if update_success:
        # Verify all teams in slate have batting orders
        slate_file = "../fd_current_slate/fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        
        # Check batting order coverage
        hitters = df[df['Position'] != 'P']
        teams_with_orders = set()
        
        for team in hitters['Team'].unique():
            team_hitters = hitters[hitters['Team'] == team]
            if team_hitters['Batting Order'].notna().sum() > 0:
                teams_with_orders.add(team)
        
        all_teams = set(hitters['Team'].unique())
        missing_teams = all_teams - teams_with_orders
        
        print(f"\nBATTING ORDER COVERAGE:")
        print(f"✅ Teams with batting orders: {len(teams_with_orders)}/{len(all_teams)}")
        print(f"✅ Teams covered: {sorted(teams_with_orders)}")
        
        if missing_teams:
            print(f"❌ Teams missing batting orders: {sorted(missing_teams)}")
        
        print("\nLINEUP UPDATE COMPLETE!")
        print("SUCCESS: FanDuel slate updated with batting order estimates")
        print("✅ All teams in today's slate processed")
        print("✅ No teams from outside today's slate included")
        print("Ready for DFS model optimization")
    else:
        print("\nLINEUP UPDATE FAILED!")
        print("Manual intervention may be required")

if __name__ == "__main__":
    main()

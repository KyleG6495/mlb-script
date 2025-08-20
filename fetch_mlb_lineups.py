#!/usr/bin/env python3
"""
MLB.COM OFFICIAL LINEUP FETCHER
===============================
Fetch confirmed starting lineups from MLB.com's official API.
This is more reliable than Rotowire as it uses MLB's actual data.
"""

import requests
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_todays_games():
    """Get today's MLB games from the official MLB API"""
    
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"API Response structure: {list(data.keys())}")
        
        games = []
        dates = data.get('dates', [])
        
        if not dates:
            logger.warning("No games found in dates array")
            return []
        
        for date_entry in dates:
            for game in date_entry.get('games', []):
                try:
                    # Extract team info more carefully
                    away_team = game.get('teams', {}).get('away', {}).get('team', {})
                    home_team = game.get('teams', {}).get('home', {}).get('team', {})
                    
                    away_abbr = away_team.get('abbreviation') or away_team.get('teamCode') or 'UNK'
                    home_abbr = home_team.get('abbreviation') or home_team.get('teamCode') or 'UNK'
                    
                    if away_abbr != 'UNK' and home_abbr != 'UNK':
                        games.append({
                            'game_pk': game['gamePk'],
                            'away_team': away_abbr,
                            'home_team': home_abbr,
                            'game_time': game.get('gameDate', ''),
                            'status': game.get('status', {}).get('detailedState', '')
                        })
                        logger.info(f"Found game: {away_abbr} @ {home_abbr}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing game: {e}")
                    continue
        
        logger.info(f"Found {len(games)} games for {today}")
        return games
        
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        logger.error(f"Response content: {response.text[:500] if 'response' in locals() else 'No response'}")
        return []

def get_game_lineups(game_pk):
    """Get confirmed lineups for a specific game"""
    
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        lineups = {'away': [], 'home': []}
        
        # Get team info
        away_team = data.get('gameData', {}).get('teams', {}).get('away', {}).get('abbreviation', '')
        home_team = data.get('gameData', {}).get('teams', {}).get('home', {}).get('abbreviation', '')
        
        # Try to get lineups from liveData
        live_data = data.get('liveData', {})
        boxscore = live_data.get('boxscore', {})
        
        # Check both teams
        for team_type in ['away', 'home']:
            team_data = boxscore.get('teams', {}).get(team_type, {})
            team_abbr = away_team if team_type == 'away' else home_team
            
            # Get batting order
            batting_order = team_data.get('battingOrder', [])
            
            if batting_order:
                logger.info(f"Found {len(batting_order)} batters for {team_abbr}")
                
                for i, player_id in enumerate(batting_order):
                    player_info = team_data.get('players', {}).get(f'ID{player_id}', {})
                    if player_info:
                        player_name = player_info.get('person', {}).get('fullName', '')
                        position = player_info.get('position', {}).get('abbreviation', '')
                        
                        if player_name:
                            lineups[team_type].append({
                                'team': team_abbr,
                                'batting_order': i + 1,
                                'player_name': player_name,
                                'position': position,
                                'player_id': player_id
                            })
            
            # Also get starting pitcher
            pitchers = team_data.get('players', {})
            for player_key, player_info in pitchers.items():
                if player_info.get('position', {}).get('abbreviation') == 'P':
                    # Check if this is the starting pitcher
                    stats = player_info.get('stats', {}).get('pitching', {})
                    if stats and stats.get('inningsPitched', '0') != '0':
                        pitcher_name = player_info.get('person', {}).get('fullName', '')
                        if pitcher_name:
                            lineups[team_type].append({
                                'team': team_abbr,
                                'batting_order': 0,  # Pitchers don't bat in AL
                                'player_name': pitcher_name,
                                'position': 'P',
                                'player_id': player_key.replace('ID', '')
                            })
                            break
        
        return lineups
        
    except Exception as e:
        logger.error(f"Error fetching lineup for game {game_pk}: {e}")
        return {'away': [], 'home': []}

def fetch_all_lineups():
    """Fetch all confirmed lineups for today's games"""
    
    logger.info("🏟️ Fetching official MLB lineups...")
    
    games = get_todays_games()
    if not games:
        logger.warning("No games found for today")
        return {}
    
    all_lineups = {}
    
    for game in games:
        logger.info(f"Fetching lineup for {game['away_team']} @ {game['home_team']}...")
        
        lineups = get_game_lineups(game['game_pk'])
        
        # Combine away and home lineups
        for team_lineups in lineups.values():
            for player in team_lineups:
                team = player['team']
                if team not in all_lineups:
                    all_lineups[team] = []
                all_lineups[team].append(player)
        
        time.sleep(0.5)  # Be respectful to MLB's API
    
    logger.info(f"📊 Collected lineups for {len(all_lineups)} teams")
    for team, players in all_lineups.items():
        hitters = [p for p in players if p['position'] != 'P']
        pitchers = [p for p in players if p['position'] == 'P']
        logger.info(f"   {team}: {len(pitchers)} pitcher(s), {len(hitters)} hitters")
    
    return all_lineups

def match_with_fd_slate(mlb_lineups):
    """Match MLB lineups with FanDuel slate players"""
    
    try:
        # Load FD slate
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📋 Loaded FD slate with {len(fd_df)} players")
        
        confirmed_starters = []
        
        for team, mlb_players in mlb_lineups.items():
            logger.info(f"\n🏟️ Processing {team}...")
            
            # Get FD players for this team
            fd_team_players = fd_df[fd_df['Team'] == team]
            
            if len(fd_team_players) == 0:
                logger.warning(f"   ⚠️ No FD players found for {team}")
                continue
            
            # Match each MLB player with FD player
            matched_count = 0
            
            for mlb_player in mlb_players:
                mlb_name = mlb_player['player_name']
                mlb_position = mlb_player['position']
                batting_order = mlb_player['batting_order']
                
                # Filter FD players by position
                if mlb_position == 'P':
                    fd_candidates = fd_team_players[fd_team_players['Position'] == 'P']
                else:
                    fd_candidates = fd_team_players[fd_team_players['Position'] != 'P']
                
                # Try to match by name
                best_match = None
                best_score = 0
                
                for _, fd_player in fd_candidates.iterrows():
                    fd_full_name = f"{fd_player['First Name']} {fd_player['Nickname']}"
                    
                    # Calculate match score
                    score = 0
                    
                    # Exact match
                    if mlb_name.lower() == fd_full_name.lower():
                        score = 100
                    # Last name match
                    elif mlb_name.split()[-1].lower() == fd_player['Nickname'].lower():
                        score = 80
                    # First name + last name match
                    elif all(part.lower() in fd_full_name.lower() for part in mlb_name.split()):
                        score = 70
                    # Partial match
                    elif any(part.lower() in fd_full_name.lower() for part in mlb_name.split() if len(part) > 3):
                        score = 50
                    
                    if score > best_score:
                        best_score = score
                        best_match = fd_player
                
                # If we found a good match, add to confirmed starters
                if best_match is not None and best_score >= 50:
                    starter = best_match.copy()
                    starter['Batting Order'] = batting_order
                    starter['MLB_Confirmed'] = True
                    starter['MLB_Name'] = mlb_name
                    
                    confirmed_starters.append(starter)
                    matched_count += 1
                    
                    if mlb_position == 'P':
                        logger.info(f"   ⚾ Pitcher: {fd_player['Nickname']} ← {mlb_name}")
                    else:
                        logger.info(f"   ✅ {batting_order}. {fd_player['Nickname']} ← {mlb_name}")
                else:
                    logger.warning(f"   ❌ No match for {mlb_name} ({mlb_position})")
            
            logger.info(f"   📊 {team}: {matched_count}/{len(mlb_players)} players matched")
        
        if confirmed_starters:
            # Save to file
            confirmed_df = pd.DataFrame(confirmed_starters)
            output_file = 'mlb_confirmed_starters.csv'
            confirmed_df.to_csv(output_file, index=False)
            
            logger.info(f"\n💾 Saved {len(confirmed_starters)} confirmed starters to {output_file}")
            
            # Show summary
            teams_with_lineups = confirmed_df['Team'].unique()
            logger.info(f"📊 Teams with confirmed lineups: {sorted(teams_with_lineups)}")
            
            return output_file
        else:
            logger.error("❌ No confirmed starters found")
            return None
            
    except Exception as e:
        logger.error(f"Error matching lineups: {e}")
        return None

def main():
    """Main function"""
    
    print("🏟️ MLB OFFICIAL LINEUP FETCHER")
    print("=" * 50)
    print("Fetching confirmed starting lineups from MLB.com")
    print()
    
    # Fetch lineups from MLB API
    mlb_lineups = fetch_all_lineups()
    
    if not mlb_lineups:
        print("❌ No lineups found from MLB.com")
        return False
    
    # Match with FD slate
    output_file = match_with_fd_slate(mlb_lineups)
    
    if output_file:
        print(f"\n✅ SUCCESS: Confirmed lineups saved to {output_file}")
        print("🎯 Use this file for accurate starting lineup projections")
        return True
    else:
        print("\n❌ FAILED: Could not match lineups with FD slate")
        return False

if __name__ == "__main__":
    main()

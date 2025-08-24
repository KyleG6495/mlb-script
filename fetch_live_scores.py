#!/usr/bin/env python3
"""
MLB LIVE SCORES FETCHER
======================
Fetch live game scores and status for today's slate
"""

import requests
import json
from datetime import datetime
import pandas as pd

def fetch_mlb_scores():
    """Fetch live MLB scores from MLB Stats API"""
    try:
        # Get today's date in format needed for MLB API
        today = datetime.now().strftime("%Y-%m-%d")
        
        # MLB Stats API endpoint for today's games
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=game(content(summary)),linescore"
        
        print(f"Fetching MLB scores for {today}...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        games_data = []
        
        if 'dates' in data and data['dates']:
            games = data['dates'][0].get('games', [])
            
            print(f"Found {len(games)} MLB games today")
            
            for game in games:
                try:
                    # Extract game information
                    game_pk = game.get('gamePk', '')
                    game_date = game.get('gameDate', '')
                    
                    # Teams - need to map team names to abbreviations
                    team_map = {
                        'Athletics': 'OAK', 'Minnesota Twins': 'MIN', 'Texas Rangers': 'TEX',
                        'Kansas City Royals': 'KC', 'Milwaukee Brewers': 'MIL', 'Chicago Cubs': 'CHC',
                        'Los Angeles Dodgers': 'LAD', 'Colorado Rockies': 'COL', 'New York Mets': 'NYM',
                        'Washington Nationals': 'WSH', 'San Francisco Giants': 'SF', 'San Diego Padres': 'SD',
                        'Houston Astros': 'HOU', 'Baltimore Orioles': 'BAL', 'Boston Red Sox': 'BOS',
                        'New York Yankees': 'NYY', 'St. Louis Cardinals': 'STL', 'Tampa Bay Rays': 'TB',
                        'Oakland Athletics': 'OAK'
                    }
                    
                    away_team_name = game['teams']['away']['team']['name']
                    home_team_name = game['teams']['home']['team']['name']
                    away_team = team_map.get(away_team_name, away_team_name[:3].upper())
                    home_team = team_map.get(home_team_name, home_team_name[:3].upper())
                    
                    # Scores
                    away_score = game['teams']['away'].get('score', 0) or 0
                    home_score = game['teams']['home'].get('score', 0) or 0
                    
                    # Game status
                    status = game['status']['detailedState']
                    status_code = game['status']['statusCode']
                    
                    # Inning information
                    inning = ""
                    if 'linescore' in game and game['linescore']:
                        current_inning = game['linescore'].get('currentInning', 1)
                        inning_state = game['linescore'].get('inningState', 'Middle')
                        
                        if status_code in ['I', 'IR']:  # In progress
                            inning_half = "T" if inning_state == "Top" else "B"
                            inning = f"{inning_half}{current_inning}"
                        elif status_code == 'F':  # Final
                            if current_inning > 9:
                                inning = f"F/{current_inning}"
                            else:
                                inning = "F"
                        else:
                            inning = status
                    else:
                        inning = status
                    
                    # Game display name
                    game_display = f"{away_team}@{home_team}"
                    
                    # Determine if game is on our slate
                    slate_teams = {'BAL', 'BOS', 'HOU', 'NYM', 'NYY', 'SD', 'SF', 'STL', 'TB', 'WSH'}
                    on_slate = away_team in slate_teams or home_team in slate_teams
                    
                    game_info = {
                        'game_pk': game_pk,
                        'game': game_display,
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': away_score,
                        'home_score': home_score,
                        'status': status,
                        'status_code': status_code,
                        'inning': inning,
                        'game_date': game_date,
                        'on_slate': on_slate,
                        'last_updated': datetime.now().strftime("%H:%M:%S")
                    }
                    
                    games_data.append(game_info)
                    
                    slate_indicator = "[SLATE]" if on_slate else "      "
                    print(f"{slate_indicator} {game_display}: {away_score}-{home_score} ({inning})")
                    
                except Exception as e:
                    print(f"Error processing game: {e}")
                    continue
        
        # Save to JSON file
        output_file = "live_scores_today.json"
        with open(output_file, 'w') as f:
            json.dump({
                'games': games_data,
                'last_updated': datetime.now().isoformat(),
                'total_games': len(games_data),
                'slate_games': len([g for g in games_data if g['on_slate']])
            }, f, indent=2)
        
        print(f"\\nSaved {len(games_data)} games to {output_file}")
        slate_games = [g for g in games_data if g['on_slate']]
        print(f"Found {len(slate_games)} games on tonight's DFS slate")
        
        return True
        
    except requests.RequestException as e:
        print(f"Error fetching MLB scores: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting MLB live scores fetch...")
    success = fetch_mlb_scores()
    
    if success:
        print("SUCCESS: Live scores fetched successfully!")
    else:
        print("ERROR: Failed to fetch live scores")

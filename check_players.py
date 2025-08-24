#!/usr/bin/env python3
import requests
import json

# Get the games for July 22, 2025  
url = 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2025-07-22&hydrate=boxscore'
response = requests.get(url)
data = response.json()

print('Searching for Rich Hill and Logan Gilbert in game data...')

for date_data in data.get('dates', []):
    for game in date_data.get('games', []):
        try:
            boxscore = game.get('boxscore', {})
            teams = boxscore.get('teams', {})
            
            for side in ['away', 'home']:
                team_data = teams.get(side, {})
                players = team_data.get('players', {})
                
                for player_id, player_data in players.items():
                    person = player_data.get('person', {})
                    name = person.get('fullName', '')
                    
                    if 'Rich Hill' in name or 'Logan Gilbert' in name:
                        print(f'\n=== {name} ===')
                        
                        # Pitching stats
                        pitching_stats = player_data.get('stats', {}).get('pitching', {})
                        if pitching_stats:
                            print('Pitching Stats:')
                            print(f'  IP: {pitching_stats.get("inningsPitched", "N/A")}')
                            print(f'  SO: {pitching_stats.get("strikeOuts", "N/A")}')
                            print(f'  BB: {pitching_stats.get("baseOnBalls", "N/A")}')
                            print(f'  H: {pitching_stats.get("hits", "N/A")}')
                            print(f'  ER: {pitching_stats.get("earnedRuns", "N/A")}')
                            print(f'  W: {pitching_stats.get("wins", "N/A")}')
                            print(f'  L: {pitching_stats.get("losses", "N/A")}')
                            
                            # Calculate FanDuel points manually
                            ip = float(pitching_stats.get("inningsPitched", "0"))
                            so = int(pitching_stats.get("strikeOuts", "0"))
                            bb = int(pitching_stats.get("baseOnBalls", "0"))
                            hits = int(pitching_stats.get("hits", "0"))
                            er = int(pitching_stats.get("earnedRuns", "0"))
                            wins = int(pitching_stats.get("wins", "0"))
                            
                            fd_points = (ip * 2.25) + (so * 3.0) + (wins * 6.0) - (er * 3.0) - (hits * 0.6) - (bb * 0.6)
                            print(f'  Calculated FD Points: {fd_points:.2f}')
                            
        except Exception as e:
            continue

print('Done searching.')

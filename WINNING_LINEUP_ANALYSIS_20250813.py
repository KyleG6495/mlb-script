#!/usr/bin/env python3
"""
WINNING LINEUP ANALYSIS - AUGUST 13TH
Reverse-engineer the top 5 winning lineups to identify patterns
"""

import pandas as pd
import numpy as np

def analyze_winning_lineups():
    """Analyze the top 5 winning lineups from August 13th"""
    
    # Top 5 winning lineups data
    winning_lineups = [
        {
            'rank': 1, 'user': 'satans6kat', 'score': 271.6, 'prize': 50.00,
            'P': ('Eury Perez', 33.0, 'MIA', 2.2, 6000),  # (name, points, team, ownership, salary)
            'C': ('Will Smith', 31.7, 'LAD', 7.3, 3400),
            '2B': ('Otto Lopez', 9.2, 'MIA', 1.2, 2500),
            '3B': ('Eugenio Suarez', 15.2, 'SEA', 4.9, 3000),
            'SS': ('Xavier Edwards', 30.9, 'MIA', 4.5, 3100),
            'OF1': ('Kyle Stowers', 25.1, 'MIA', 3.7, 3200),
            'OF2': ('Jakob Marsee', 69.9, 'MIA', 1.1, 2000),
            'OF3': ('Cody Bellinger', 21.7, 'MIN', 3.8, 3400),
            'UTIL': ('Junior Caminero', 34.9, 'TB', 25.9, 3600),
            'total_salary': 33200
        },
        {
            'rank': 2, 'user': 'iamstreet', 'score': 234.5, 'prize': 25.00,
            'P': ('Trevor Rogers', 40.0, 'SEA', 3.1, 10600),
            'C': ('Liam Hicks', 21.9, 'MIA', 0.4, 2500),
            '2B': ('Jose Altuve', 6.2, 'BOS', 19.1, 3200),
            '3B': ('Graham Pauley', 33.9, 'MIA', 0.7, 2000),
            'SS': ('Xavier Edwards', 30.9, 'MIA', 4.5, 3100),
            'OF1': ('Jakob Marsee', 69.9, 'MIA', 1.1, 2000),
            'OF2': ('Aaron Judge', 0.0, 'MIN', 7.9, 4700),
            'OF3': ('Eli White', 0.0, 'ATL', 0.5, 2000),
            'UTIL': ('Jurickson Profar', 31.7, 'ATL', 2.3, 3000),
            'total_salary': 33100
        },
        {
            'rank': 3, 'user': 'mwarman22', 'score': 230.9, 'prize': 15.00,
            'P': ('Joe Ryan', 48.0, 'MIN', 2.9, 10000),
            'C': ('Matt Olson', 12.4, 'ATL', 1.6, 3500),
            '2B': ('Brandon Lowe', 22.2, 'TB', 45.4, 3000),
            '3B': ('Junior Caminero', 34.9, 'TB', 25.9, 3600),
            'SS': ('Jeremy Pena', 18.7, 'BOS', 13.0, 3200),
            'OF1': ('Chandler Simpson', 15.4, 'TB', 16.7, 2700),
            'OF2': ('Marcell Ozuna', 34.9, 'ATL', 2.7, 3200),
            'OF3': ('Michael Harris II', 35.4, 'ATL', 0.6, 3000),
            'UTIL': ('Yandy Diaz', 9.0, 'TB', 7.8, 3100),
            'total_salary': 35300
        },
        {
            'rank': 4, 'user': 'wethebestbet', 'score': 224.5, 'prize': 12.00,
            'P': ('Logan Gilbert', 35.0, 'SEA', 36.4, 9800),
            'C': ('Pete Alonso', 19.0, 'ATL', 33.1, 3600),
            '2B': ('Jeff McNeil', 12.5, 'ATL', 5.6, 2800),
            '3B': ('Nacho Alvarez Jr.', 6.2, 'ATL', 2.1, 2000),
            'SS': ('Francisco Lindor', 21.4, 'ATL', 35.4, 3800),
            'OF1': ('Juan Soto', 28.4, 'ATL', 29.1, 4200),
            'OF2': ('Marcell Ozuna', 34.9, 'ATL', 2.7, 3200),
            'OF3': ('Michael Harris II', 35.4, 'ATL', 0.6, 3000),
            'UTIL': ('Jurickson Profar', 31.7, 'ATL', 2.3, 3000),
            'total_salary': 35400
        },
        {
            'rank': 5, 'user': 'foxygrandpa252', 'score': 223.1, 'prize': 10.00,
            'P': ('Hunter Brown', 39.0, 'BOS', 11.3, 10300),
            'C': ('Liam Hicks', 21.9, 'MIA', 0.4, 2500),
            '2B': ('Xavier Edwards', 30.9, 'MIA', 4.5, 3100),
            '3B': ('Graham Pauley', 33.9, 'MIA', 0.7, 2000),
            'SS': ('Francisco Lindor', 21.4, 'ATL', 35.4, 3800),
            'OF1': ('Kyle Stowers', 25.1, 'MIA', 3.7, 3200),
            'OF2': ('Cedric Mullins', 3.5, 'ATL', 10.4, 2800),
            'OF3': ('Juan Soto', 28.4, 'ATL', 29.1, 4200),
            'UTIL': ('Pete Alonso', 19.0, 'ATL', 33.1, 3600),
            'total_salary': 35500
        }
    ]
    
    print("LINEUP: WINNING LINEUP ANALYSIS - AUGUST 13TH")
    print("=" * 60)
    print()
    
    # Key insights
    all_players = []
    miami_stack_count = 0
    atlanta_stack_count = 0
    tampa_stack_count = 0
    
    for lineup in winning_lineups:
        print(f"#{lineup['rank']} - {lineup['user']} ({lineup['score']} pts, ${lineup['prize']:.2f})")
        
        # Team analysis
        teams = {}
        miami_players = 0
        atlanta_players = 0 
        tampa_players = 0
        
        for pos in ['P', 'C', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL']:
            name, points, team, ownership, salary = lineup[pos]
            teams[team] = teams.get(team, 0) + 1
            all_players.append((name, points, team, ownership, salary, pos))
            
            if team == 'MIA':
                miami_players += 1
            elif team == 'ATL':
                atlanta_players += 1
            elif team == 'TB':
                tampa_players += 1
        
        print(f"  Miami: {miami_players} players, Atlanta: {atlanta_players} players, Tampa: {tampa_players} players")
        
        if miami_players >= 3:
            miami_stack_count += 1
        if atlanta_players >= 3:
            atlanta_stack_count += 1
        if tampa_players >= 3:
            tampa_stack_count += 1
            
        print(f"  Salary: ${lineup['total_salary']:,}")
        print()
    
    # Overall patterns
    print("TARGET: KEY WINNING PATTERNS:")
    print("=" * 40)
    print(f"DATA: Miami stacks (3+): {miami_stack_count}/5 lineups")
    print(f"DATA: Atlanta stacks (3+): {atlanta_stack_count}/5 lineups") 
    print(f"DATA: Tampa stacks (3+): {tampa_stack_count}/5 lineups")
    print()
    
    # Most popular players
    player_count = {}
    for name, points, team, ownership, salary, pos in all_players:
        if name in player_count:
            player_count[name]['count'] += 1
            player_count[name]['total_points'] += points
        else:
            player_count[name] = {
                'count': 1, 
                'total_points': points,
                'team': team,
                'ownership': ownership,
                'salary': salary,
                'position': pos
            }
    
    print(" MOST POPULAR WINNING PLAYERS:")
    print("=" * 40)
    for name, data in sorted(player_count.items(), key=lambda x: x[1]['count'], reverse=True):
        if data['count'] > 1:
            avg_points = data['total_points'] / data['count']
            print(f"{name} ({data['team']}) - {data['count']}/5 lineups, {avg_points:.1f} avg pts, {data['ownership']:.1f}% owned")
    
    print()
    print(" HIGHEST SCORING PLAYERS:")
    print("=" * 40)
    for name, points, team, ownership, salary, pos in sorted(all_players, key=lambda x: x[1], reverse=True)[:10]:
        print(f"{name} ({team}, {pos}) - {points:.1f} pts, {ownership:.1f}% owned, ${salary}")
    
    print()
    print(" CONTRARIAN GEMS (<5% ownership):")
    print("=" * 40)
    for name, points, team, ownership, salary, pos in sorted(all_players, key=lambda x: x[1], reverse=True):
        if ownership < 5.0 and points > 20:
            print(f"{name} ({team}, {pos}) - {points:.1f} pts, {ownership:.1f}% owned, ${salary}")

if __name__ == "__main__":
    analyze_winning_lineups()

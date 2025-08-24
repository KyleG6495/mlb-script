#!/usr/bin/env python3
"""
DEBUG ROTOWIRE HTML STRUCTURE
============================
Analyze the actual HTML structure from Rotowire to understand why we're not extracting players.
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_rotowire_structure():
    """Debug the actual HTML structure of Rotowire lineups"""
    
    url = "https://www.rotowire.com/baseball/daily-lineups.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("Fetching Rotowire page for HTML analysis...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find game containers
        game_containers = soup.find_all('div', class_='lineup__box')
        print(f"Found {len(game_containers)} game containers")
        
        if game_containers:
            container = game_containers[0]  # Analyze first container
            print(f"\n=== ANALYZING FIRST GAME CONTAINER ===")
            print(f"Container classes: {container.get('class', [])}")
            
            # Look for team information
            team_abbrs = container.find_all('div', class_='lineup__abbr')
            print(f"Team abbreviations found: {len(team_abbrs)}")
            for i, abbr in enumerate(team_abbrs):
                print(f"  Team {i+1}: '{abbr.get_text().strip()}'")
            
            # Look for team sections
            team_sections = container.find_all('div', class_=re.compile(r'lineup__(visit|home)'))
            print(f"Team sections (visit/home): {len(team_sections)}")
            
            if not team_sections:
                team_sections = container.find_all('div', class_=re.compile(r'lineup__team'))
                print(f"Team sections (general): {len(team_sections)}")
            
            if not team_sections:
                lineup_groups = container.find_all('ul', class_='lineup__list')
                print(f"Lineup groups (ul.lineup__list): {len(lineup_groups)}")
                team_sections = lineup_groups
            
            # Look for player elements
            player_elements = container.find_all('li', class_='lineup__player')
            print(f"Player elements found: {len(player_elements)}")
            
            if player_elements:
                print(f"\n=== ANALYZING FIRST FEW PLAYERS ===")
                for i, player_elem in enumerate(player_elements[:5]):
                    print(f"\nPlayer {i+1}:")
                    print(f"  Classes: {player_elem.get('class', [])}")
                    print(f"  Text content: '{player_elem.get_text().strip()}'")
                    
                    # Look for position
                    pos_div = player_elem.find('div', class_='lineup__pos')
                    if pos_div:
                        print(f"  Position: '{pos_div.get_text().strip()}'")
                    else:
                        print(f"  Position div not found")
                    
                    # Look for name divs
                    name_divs = player_elem.find_all('div')
                    print(f"  All divs in player element:")
                    for j, div in enumerate(name_divs):
                        div_classes = div.get('class', [])
                        div_text = div.get_text().strip()
                        print(f"    Div {j+1}: classes={div_classes}, text='{div_text}'")
            
            # Look at the overall structure
            print(f"\n=== CONTAINER STRUCTURE OVERVIEW ===")
            print(f"Container HTML (first 500 chars):")
            print(container.prettify()[:500])
            print("...")
            
            # Check if there are any other patterns
            all_divs = container.find_all('div')
            print(f"\nTotal divs in container: {len(all_divs)}")
            
            # Look for specific patterns
            lineup_related = container.find_all(class_=re.compile(r'lineup'))
            print(f"All lineup-related elements: {len(lineup_related)}")
            
            unique_classes = set()
            for elem in lineup_related:
                classes = elem.get('class', [])
                for cls in classes:
                    if 'lineup' in cls:
                        unique_classes.add(cls)
            
            print(f"Unique lineup classes found: {sorted(unique_classes)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rotowire_structure()

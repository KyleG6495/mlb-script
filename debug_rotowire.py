#!/usr/bin/env python3
"""
Debug script to examine Rotowire HTML structure
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_rotowire_structure():
    """Debug the actual HTML structure of Rotowire"""
    
    url = "https://www.rotowire.com/baseball/daily-lineups.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Fetching Rotowire page for structure analysis...")
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Save raw HTML for inspection
    with open('rotowire_raw.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("Saved raw HTML to rotowire_raw.html")
    
    # Look for any elements containing "Confirmed Lineup"
    confirmed_elements = soup.find_all(text=re.compile(r'Confirmed Lineup', re.I))
    print(f"\nFound {len(confirmed_elements)} 'Confirmed Lineup' text elements")
    
    for i, element in enumerate(confirmed_elements[:3]):  # Show first 3
        print(f"\nConfirmed Lineup #{i+1}:")
        parent = element.parent if element.parent else element
        print(f"Parent tag: {parent.name if hasattr(parent, 'name') else 'text'}")
        
        # Get surrounding context
        if hasattr(parent, 'get_text'):
            context = parent.get_text()[:500]  # First 500 chars
            print(f"Context: {context}")
        
        # Look for lineup data around this element
        if hasattr(parent, 'find_next_siblings'):
            siblings = parent.find_next_siblings()[:5]
            for j, sibling in enumerate(siblings):
                if hasattr(sibling, 'get_text'):
                    sibling_text = sibling.get_text().strip()
                    if sibling_text:
                        print(f"  Sibling {j+1}: {sibling_text[:100]}")
    
    # Look for specific lineup containers
    print("\n" + "="*50)
    print("SEARCHING FOR LINEUP CONTAINERS")
    
    # Try different container patterns
    containers = []
    
    # Pattern 1: Look for div elements with lineup-related classes
    lineup_divs = soup.find_all('div', class_=re.compile(r'lineup|game|match', re.I))
    containers.extend([(div, 'class-based') for div in lineup_divs])
    
    # Pattern 2: Look for elements containing team abbreviations
    team_pattern = r'\b(ARI|ATL|BAL|BOS|CHC|CIN|CLE|COL|CWS|KC|LAA|LAD|MIL|NYM|NYY|OAK|PHI|PIT|SD|SF|SEA|STL|TB|TEX|TOR|WSH|DET|HOU|MIN|MIA)\b'
    team_elements = soup.find_all(text=re.compile(team_pattern))
    
    for element in team_elements[:10]:  # First 10
        parent = element.parent
        if parent and hasattr(parent, 'get_text'):
            text = parent.get_text()
            if 'lineup' in text.lower() or 'confirmed' in text.lower():
                containers.append((parent, 'team-based'))
    
    print(f"Found {len(containers)} potential containers")
    
    # Analyze container content
    for i, (container, source) in enumerate(containers[:5]):  # First 5
        print(f"\nContainer #{i+1} ({source}):")
        if hasattr(container, 'get_text'):
            text = container.get_text()
            print(f"Length: {len(text)} chars")
            print(f"Preview: {text[:200]}")
            
            # Look for batting order patterns
            batting_patterns = [
                r'\d+\.\s*[A-Z]{2,3}\s+[A-Za-z\s\.]+',  # "1. CF Player Name"
                r'[A-Z]{2,3}\s+[A-Za-z\s\.]+',          # "CF Player Name"
                r'[A-Za-z\s\.]+\s+[A-Z]{2,3}',          # "Player Name CF"
            ]
            
            for pattern in batting_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    print(f"  Pattern '{pattern}' found {len(matches)} matches:")
                    for match in matches[:3]:  # First 3
                        print(f"    {match}")

if __name__ == "__main__":
    debug_rotowire_structure()

#!/usr/bin/env python3
"""
TEST CONFIRMED STARTERS - Debug version
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_analysis():
    """Test the analysis step by step"""
    print("TARGET: TESTING CONFIRMED STARTERS SYSTEM")
    print("=" * 60)
    
    try:
        print("Step 1: Loading FD slate...")
        
        # Load FD slate with encoding handling
        try:
            fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv', encoding='utf-8')
        except UnicodeDecodeError:
            try:
                fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv', encoding='cp1252')
            except UnicodeDecodeError:
                fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv', encoding='latin-1')
        
        print(f"SUCCESS: Loaded FD slate: {len(fd_df)} players")
        print(f"Columns: {list(fd_df.columns)}")
        
        # Get unique games
        games = fd_df['Game'].unique()
        print(f" Games detected: {list(games)}")
        
        # Get probable starters
        probable_starters = fd_df[
            (fd_df['Position'] == 'P') & 
            (fd_df['Probable Pitcher'] == 'Yes')
        ]
        
        print(f"BASEBALL: PROBABLE STARTING PITCHERS: {len(probable_starters)}")
        for _, pitcher in probable_starters.iterrows():
            print(f"   SUCCESS: {pitcher['Nickname']} ({pitcher['Team']}) - ${pitcher['Salary']:,}")
        
        # Test RotoWire connection
        print("\nStep 2: Testing RotoWire connection...")
        try:
            url = "https://www.rotowire.com/baseball/daily-lineups.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            print(f"SUCCESS: RotoWire response: {response.status_code}")
            print(f"Content length: {len(response.content)} bytes")
            
        except Exception as e:
            print(f"ERROR: RotoWire error: {e}")
        
        print("\nCOMPLETE: TEST COMPLETE!")
        
    except Exception as e:
        print(f"ERROR: Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis()

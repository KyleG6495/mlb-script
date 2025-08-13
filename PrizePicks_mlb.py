#!/usr/bin/env python3
r"""
PrizePicks_mlb.py  –  API version (updated output path, May 2025)
========================================================
Fetch today’s MLB prop lines from PrizePicks API for league ID 2 (MLB) and save
them as Excel workbooks for downstream scripts (`compare_to_lines.py`) to merge
with model projections.

Output
------
    C:\MLB_Project\data\lines\pp_mlb_lines\PP_mlb_picks_YYYYMMDD_HHMMSS.xlsx
    C:\MLB_Project\data\lines\pp_mlb_lines\PrizePicks_MLB.xlsx (fixed path for comparison)

Usage
-----
    python C:\MLB_Project\scripts\PrizePicks_mlb.py

Dependencies
------------
    requests, pandas, datetime, os, logging
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API URL for MLB (league_id=2)
url = "https://api.prizepicks.com/projections?league_id=2&per_page=250&single_stat=true&in_game=true"

# Headers (Copied from cURL)
headers = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,af;q=0.8,ak;q=0.7,eo;q=0.6",
    "Content-Type": "application/json",
    "Origin": "https://app.prizepicks.com",
    "Priority": "u=1, i",
    "Referer": "https://app.prizepicks.com/",
    "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "X-Device-Id": "9453d474-310f-443d-85b6-5ee994f21d5e",
    "X-Device-Info": "name=,os=windows,osVersion=Windows NT 10.0; Win64; x64,isSimulator=false,platform=web,appVersion=web"
}

# Cookies (Copied from cURL)
cookies = {
    "rl_anonymous_id": "RS_ENC_v3_IjEyMGJiZDM2LTE0NjItNDQ2ZC05ZmMwLWZkOGQ0NmE3OWZiYyI%3D",
    "rl_page_init_referrer": "RS_ENC_v3_IiRkaXJlY3Qi",
    "pxcts": "2d98e8f1-fda2-11ef-9e9a-abcb9f8a2ef9",
    "_pxvid": "2d98de9a-fda2-11ef-9e9a-c65a0936718b",
    "__pxvid": "2e6f27bc-fda2-11ef-8840-0242ac120003",
    "_gcl_au": "1.1.763709346.1741605855",
    "_tt_enable_cookie": "1",
    "_ttp": "01JNZWS233J55VJAFF7R3GTMRB_.tt.1",
    "__podscribe_prizepicks_referrer": "_",
    "__podscribe_prizepicks_landing_url": "https://app.prizepicks.com/",
    "__podscribe_did": "pscrb_c4832e0f-0d62-425e-e8f2-7fe27f21fbe4",
    "_scid": "Qm_7F2vbYGrOxlASI2F4NVt0t5Tn1T9y",
    "intercom-id-qmdeaj0t": "129be5fd-c2f3-4e41-9bd2-3781e6a71996",
    "intercom-session-qmdeaj0t": "",
    "intercom-device-id-qmdeaj0t": "c7b0382e-bb7d-420c-b987-ee44e6a981ca",
    "_ScCbts": "[]",
    "rl_trait": "RS_ENC_v3_eyJsYXN0X29wZW5lZF9zdGF0ZSI6IiIsImN1c3RvbWVyRGFzaExpbmsiOiJodHRwczovL2FwaS5wcml6ZXBpY2tzLmNvbS9hZG1pbi91c2Vycy91bmRlZmluZWQiLCJsYXN0X29wZW5lZF9nYW1lX21vZGUiOiIifQ%3D%3D",
    "_sctr": "1|1741561200000",
    "_cfuvid": "vUr_ue4f6Ja4WUWbMvRWsJ7O26PDDR_dg1hrmr23KoQ-1741613022958-0.0.1.1-604800000",
    "__cf_bm": "0XSkPkcJ2oGY4sQkYjuWvRP35BQNArPNJYqNA5hbsPo-1741616695-1.0.1.1-8IGm2IJjhZ3SjTif_2wHdjLT4FwcSjR2rrborkFlMQ0vKKyWeZOlFzLduTCI9JX6kM3nWsoxASl9Hm8Rw6sDgwkFDKI_YQYGOtX49.kZT3Q",
    "cf_clearance": "vYH5Gm4Te0P6o5CW2oUlfw3hl.nPdr4hi1Q7wRRztYM-1741617280-1.2.1.1-l_5rpg_rwzee1.3tJtbmL6qy0BPMWA8jWxJTVGAuT_wUra6.VNDrVOBq0Bd8SKjWXyLABWaTIDzZZWHteH1992PyPL2Z5tNb9gU3FhhBpqebmIr2_b.8IwvAwpZTFw8UPZhWELochmbG23wH2HtHDdtYDWNJ0EYBO_cojhdW2yqf.RxT6b46tLwn8zNXwFI0PhSHdlYVqNAOV7IGFzvDE62m6cjhKJc1ws2_xOn8PE1QnvWcdfQOTkQ793DL3MulsztgGusvK6Kc5RNcRoQVOjtiRLNGUrgebAj6X4FR9UFxL.l44e9Aio2CPxtQz2jpaJE2p_WcfOkZ9hyUkN3fhlDX8GTGFvEpkDaitfOI5KsRNlcxoYXW5C5aIdymwGOwwJyiu464VoTlXTQwHC0tJlG35hGMOgBBvrXWhkZoqxc",
}

# Create session for persistent requests
session = requests.Session()
session.headers.update(headers)
session.cookies.update(cookies)

# Send request
logging.info("Fetching MLB prop lines from PrizePicks API")
response = session.get(url)

# Handle response
players_data = []
if response.status_code == 200:
    logging.info("API request successful")
    data_temp = response.json()["data"]
    info_temp = response.json()['included']
    
    # Create a dictionary to store player data with player_id as key
    player_dict = {}
    
    for i in range(len(data_temp)):
        player_id = data_temp[i]['relationships']['new_player']['data']['id']
        stat_type = data_temp[i]['attributes']['stat_type']
        line_score = data_temp[i]['attributes']['line_score']
        flag = data_temp[i]['attributes']['odds_type']
        
        # If player_id exists, update their stats, otherwise create new entry
        if flag != 'goblin':
            if player_id in player_dict:
                if stat_type not in player_dict[player_id]:
                    player_dict[player_id][stat_type] = line_score
            else:
                player_dict[player_id] = {
                    stat_type: line_score
                }
    
    # Add player names to their respective stats
    for info in info_temp:
        if info['type'] == "new_player":
            player_id = info['id']
            if player_id in player_dict:
                player_dict[player_id]['player_name'] = info['attributes']['name']
    
    # Convert dictionary values back to list
    players_data = list(player_dict.values())

    # Convert to DataFrame
    df = pd.DataFrame(players_data)
    
    # Reorder columns to put 'player_name' first
    if not df.empty:
        cols = ['player_name'] + [col for col in df.columns if col != 'player_name']
        df = df[cols]
    
    # Output paths
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    excel_filename = f"PP_mlb_picks_{timestamp}.xlsx"
    excel_path = os.path.join(output_dir, excel_filename)
    compare_path = os.path.join(output_dir, "PrizePicks_MLB.xlsx")

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save to Excel
    if not df.empty:
        df.to_excel(excel_path, index=False)
        df.to_excel(compare_path, index=False)
        logging.info(f"Success! MLB data saved to {excel_path}")
        logging.info(f"Comparison file saved to {compare_path}")
    else:
        logging.warning("No player data extracted from API response")
else:
    logging.error(f"Request failed with status code {response.status_code}")
    logging.error(f"Response: {response.text}")

# Close session
session.close()
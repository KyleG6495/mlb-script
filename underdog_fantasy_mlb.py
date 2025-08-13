#!/usr/bin/env python3
"""
underdog_fantasy_mlb.py – Selenium version (updated, July 2025)
========================================================
Scrape today's MLB pitcher AND hitter prop lines from Underdog Fantasy's pick-em page
using Selenium. Saves props to Excel and CSV for downstream scripts
(compare_to_lines.py). Includes debug output, stale element handling, and
comprehensive stat collection for both pitchers and hitters.

Output
------
    uf_mlb_picks.xlsx (all props - pitchers and hitters)
    today_pitcher_props_YYYY-MM-DD.csv (pitcher props, long format)
    mlb_raw_debug_YYYYMMDD_HHMMSS.csv (debug) python3

underdog_fantasy_mlb.py - Selenium version (updated, June 2025)
========================================================
Scrape today’s MLB pitcher prop lines from Underdog Fantasy’s pick-em page
using Selenium. Saves props to Excel and CSV for downstream scripts
(compare_to_lines.py). Includes debug output, stale element handling, and
strict pitcher stat filtering.

Output
------
    C:\\MLB_Project\\data\\lines\\uf_mlb_lines\\uf_mlb_picks.xlsx (pitcher props)
    C:\\MLB_Project\\data\\odds\\today_pitcher_props_YYYY-MM-DD.csv (pitcher props, long format)
    C:\\MLB_Project\\data\\lines\\uf_mlb_lines\\mlb_raw_debug_YYYYMMDD_HHMMSS.csv (debug)

Usage
-----
    python C:\\MLB_Project\\scripts\\underdog_fantasy_mlb.py

Dependencies
------------
    selenium, webdriver-manager, pandas, logging, time, datetime, os
"""

import time
import logging
import pandas as pd
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Output directories
OUT_DIR = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
ODDS_DIR = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ODDS_DIR, exist_ok=True)

players_data = []
raw_debug_data = []

def scrape_mlb_props():
    url = "https://underdogfantasy.com/login"

    # WebDriver Setup with Anti-Bot Measures
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    options.add_argument("--disable-webrtc")
    driver = webdriver.Chrome(options=options)

    try:
        # Login Process
        driver.get(url)
        logging.info("Navigating to login page")

        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="email_input"]'))
        )
        password_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="password_input"]'))
        )

        email_input.clear()
        password_input.clear()
        email_input.send_keys("kgoneau@gmail.com")
        password_input.send_keys("Redhairone102!")
        time.sleep(1)  # Avoid rapid input

        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="sign-in-button"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)
        time.sleep(5)  # Wait for login to complete

        logging.info("Successfully logged in, navigating to MLB picks page")
        driver.get("https://underdogfantasy.com/pick-em/higher-lower/all/mlb")
        time.sleep(3)  # Wait for page load

        # Wait for prop elements
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="over-under-cell"]'))
        )

        # Expand All "More Picks"
        def click_all_more_picks_buttons():
            try:
                buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button[class*="expandablePicksButton"], button[data-testid*="expand"], button[class*="more"]'))
                )
                for button in buttons:
                    if "more" in button.text.lower():
                        try:
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(0.5)
                        except StaleElementReferenceException:
                            logging.warning("Stale button encountered, skipping")
                logging.info("Expanded all 'More picks' buttons")
            except TimeoutException:
                logging.warning("No 'More picks' buttons found")

        click_all_more_picks_buttons()

        # Retry extraction if initial attempt fails
        max_attempts = 3  # Increased attempts
        attempt = 1
        while attempt <= max_attempts:
            logging.info(f"Extraction attempt {attempt}/{max_attempts}")
            players_data.clear()
            raw_debug_data.clear()

            # Extract Player Names and Stats
            try:
                player_elements = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="player-name"], div[class*="playerName"]'))
                )
                stat_containers = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="over-under-cell"]'))
                )
                logging.info(f"Found {len(player_elements)} players, {len(stat_containers)} stat cells")

                if len(player_elements) != len(stat_containers):
                    logging.warning(f"Mismatch: {len(player_elements)} players, {len(stat_containers)} stat cells")

                # Pitcher stats to filter
                pitcher_stats = {
                    "Pitcher Strikeouts", "Pitcher Ks", "Strikeouts", "K's",
                    "Pitching Outs", "Outs", "Innings Pitched",
                    "Hits Allowed", "Pitcher Hits Allowed",
                    "Walks Allowed", "Walks", "Bases on Balls", "BB",
                    "Earned Runs Allowed", "Earned Runs", "ER Allowed", "ER",
                    "First Earned Run Allowed", "First Strikeout",
                    "1st Inn. Hits Allowed", "1st Inn. Runs Allowed", "1st Inn. Strikeouts",
                    "1st Inn. Batters Faced", "1st Inn. Pitch Count"
                }
                batter_stats = {
                    "Hits", "Hitter Hits", "Home Runs", "RBIs", "Runs", "Total Bases",
                    "Stolen Bases", "Singles", "Batter Strikeouts", "Batter Walks", "Doubles",
                    "Hits + Runs + RBIs", "1-3 Inn. H+R+RBI", "1st Inn. H+R+RBI",
                    "1st Inn. Runs", "Fantasy Points", "1st Inn. Hits", "Triples",
                    "At Bats", "Batting Average", "On-Base Percentage", "Slugging",
                    "Hitter Fantasy Score", "Hitter Strikeouts", "Walks"
                }

                all_stat_types = set()

                for i in range(len(player_elements)):
                    # Re-fetch elements to avoid staleness
                    player_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="player-name"], div[class*="playerName"]')
                    stat_containers = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="over-under-cell"]')
                    if i >= len(player_elements) or i >= len(stat_containers):
                        logging.warning(f"Index {i} out of range after re-fetch")
                        break

                    try:
                        player_name = player_elements[i].text.strip()
                        player_data = {"player_name": player_name, "source": "UD"}
                        raw_debug_data.append({"player_name": player_name, "raw_stats": []})

                        stat_cell = stat_containers[i]
                        stat_items = stat_cell.find_elements(By.CSS_SELECTOR, 'div[class*="currentStat"], div[data-testid*="stat"], div[class*="stat"]')

                        for stat in stat_items:
                            try:
                                raw_text = stat.text.strip()
                                raw_debug_data[-1]["raw_stats"].append(raw_text)
                                
                                # Skip empty or invalid stats
                                if not raw_text or raw_text in ['0', '1', '2', 'Expired', 'Projection refreshing...']:
                                    continue

                                stat_parts = raw_text.split("\n")
                                if len(stat_parts) >= 2:
                                    stat_key = stat_parts[-1].strip()
                                    stat_value = stat_parts[0].strip()
                                elif " " in raw_text:
                                    parts = raw_text.split(" ", 1)
                                    stat_value = parts[0].strip()
                                    stat_key = parts[1].strip() if len(parts) > 1 else ""
                                else:
                                    continue  # Skip unexpected formats silently

                                all_stat_types.add(stat_key)

                                # Include both pitcher and hitter stats
                                # Only skip if it's an unknown/invalid stat type
                                valid_stats = pitcher_stats | batter_stats  # Union of both sets
                                
                                if stat_key not in valid_stats and 'Fantasy Points' not in stat_key:
                                    continue  # Skip unknown stats silently

                                try:
                                    stat_value = float(stat_value)
                                    # Only add if not already present (avoid duplicates)
                                    if stat_key not in player_data:
                                        player_data[stat_key] = stat_value
                                        logging.info(f"Processed stat: {player_name} -> {stat_key}: {stat_value}")
                                    else:
                                        logging.debug(f"Duplicate stat skipped: {player_name} -> {stat_key}: {stat_value}")
                                except ValueError:
                                    logging.warning(f"Stat value '{stat_value}' for {player_name} is not a number")
                                    continue
                            except StaleElementReferenceException:
                                logging.warning(f"Stale stat element for {player_name}, skipping")
                                continue

                        if len(player_data) > 2:
                            players_data.append(player_data)
                            logging.info(f"Saved data for {player_name}: {player_data}")
                    except StaleElementReferenceException:
                        logging.warning(f"Stale player/stat element at index {i}, skipping")
                        continue

                if players_data:
                    break
                logging.warning("No pitcher props found, retrying...")
                time.sleep(3)
                attempt += 1
            except TimeoutException:
                logging.warning("Timeout fetching elements, retrying...")
                time.sleep(3)
                attempt += 1

        # Log all stat types
        logging.info(f"All stat types found: {sorted(all_stat_types)}")

        # Save Debug Data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_filename = os.path.join(OUT_DIR, f'mlb_raw_debug_{timestamp}.csv')
        pd.DataFrame(raw_debug_data).to_csv(debug_filename, index=False)
        logging.info(f"Saved debug data to {debug_filename}")

        # Save Data
        if players_data:
            df = pd.DataFrame(players_data)
            excel_filename = os.path.join(OUT_DIR, 'uf_mlb_picks.xlsx')
            df.to_excel(excel_filename, sheet_name="props", index=False)
            logging.info(f"Data saved to {excel_filename}")

            # Save to today_pitcher_props_YYYY-MM-DD.csv in long format
            today = datetime.now().strftime('%Y-%m-%d')
            props_long = pd.melt(
                df,
                id_vars=['player_name', 'source'],
                value_vars=[col for col in df.columns if col not in ['player_name', 'source']],
                var_name='stat_type',
                value_name='line'
            ).dropna(subset=['line'])
            props_filename = os.path.join(ODDS_DIR, f'today_pitcher_props_{today}.csv')
            props_long.to_csv(props_filename, index=False)
            logging.info(f"Pitcher props saved to {props_filename}")
        else:
            logging.warning("No pitcher prop data extracted")
            raise RuntimeError(f"No MLB pitcher props found. Check {debug_filename} for raw stat types: {sorted(all_stat_types)}")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_mlb_props()
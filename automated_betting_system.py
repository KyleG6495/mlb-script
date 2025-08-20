#!/usr/bin/env python3
"""
automated_betting_system.py

Complete automated betting system that:
1. Loads your trained models from both training scripts
2. Generates daily predictions for all props
3. Scrapes current lines from PrizePicks, Underdog, etc.
4. Calculates expected value and identifies profitable bets
5. Generates betting                    elif source == 'underdog':
                        # Match Underdog format
                        for stat_name in stat_names:
                            # Ensure player_name is a string
                            if pd.isna(player_name) or not isinstance(player_name, str):
                                continue
                            matches = line_df[
                                (line_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                                (line_df['stat'] == stat_name)
                            ]
                            matching_lines.extend(matches.to_dict('records'))ndations with confidence levels

Usage:
    python automated_betting_system.py --date 2025-07-19 --min-edge 0.05
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from pathlib import Path
from scipy import stats
import warnings
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver

# Ensure we're in the correct directory for subprocess calls
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class AutomatedBettingSystem:
    def __init__(self, models_base_dir="./models"):
        self.models_base_dir = Path(models_base_dir)
        self.models = {}
        self.predictions = {}
        
        # Category mapping from your training scripts
        self.CATEGORY_MAP = {
            "hits": ("hits", "regression", "hitter"),
            "total_bases": ("totalBases", "regression", "hitter"),
            "runs": ("runs", "regression", "hitter"),
            "rbi": ("rbi", "regression", "hitter"),
            "home_runs": ("homeRuns", "regression", "hitter"),
            "hrr": ("hrr", "regression", "hitter"),
            "stolen_bases": ("stolenBases", "regression", "hitter"),
            "hr_binary": ("homeRuns_binary", "classification", "hitter"),
            "hitter_strikeouts": ("strikeOuts", "regression", "hitter"),  # NEW: Hitter being struck out
            "pitcher_strikeouts": ("strikeOuts", "regression", "pitcher"),  # Pitcher striking out batters
            "outs": ("outs", "regression", "pitcher"),
            "win_binary": ("win_binary", "classification", "pitcher"),
        }
        
    def load_all_models(self):
        """Load models from both training script formats"""
        logging.info(" Loading all trained models...")
        
        for category, (target, task_type, player_type) in self.CATEGORY_MAP.items():
            # Special case: pitcher_strikeouts uses the existing strikeouts model
            if category == "pitcher_strikeouts":
                model_dir = self.models_base_dir / "strikeouts"
            else:
                model_dir = self.models_base_dir / category
            
            # Try both model file formats (prefer newer ones)
            model_paths = [
                model_dir / f"{category}_pipeline.joblib",  # From train_prop_model.py (newer)
                model_dir / f"strikeouts_pipeline.joblib" if category == "pitcher_strikeouts" else model_dir / f"{category}_pipeline.joblib",  # Special case for pitcher strikeouts
                model_dir / f"{category}_model.pkl"  # From Train Prop Model With Holdout.py (older)
            ]
            
            model_loaded = False
            for model_path in model_paths:
                if model_path.exists():
                    try:
                        model = joblib.load(model_path)
                        self.models[category] = {
                            'model': model,
                            'target': target,
                            'task_type': task_type,
                            'player_type': player_type,
                            'path': str(model_path)
                        }
                        logging.info(f"SUCCESS: Loaded {category} model from {model_path.name}")
                        model_loaded = True
                        break
                    except Exception as e:
                        logging.warning(f"ERROR: Failed to load {category} from {model_path}: {e}")
            
            if not model_loaded:
                logging.warning(f" No model found for {category}")
        
        logging.info(f"DATA: Total models loaded: {len(self.models)}")
        return len(self.models) > 0
    
    def load_today_features(self, date_str):
        """Load feature data for today's predictions - OPTIMIZED FOR DAILY PROP ANALYSIS"""
        logging.info(f"TARGET: Loading TODAY'S CONFIRMED STARTERS ONLY for prop analysis...")
        
        # OPTIMIZATION: Use confirmed starters file to get active players only
        confirmed_starters_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_confirmed_starters_only.csv"
        active_player_ids = set()
        
        if os.path.exists(confirmed_starters_file):
            try:
                fd_slate = pd.read_csv(confirmed_starters_file)
                # Extract player IDs from the FD slate
                if 'Id' in fd_slate.columns:
                    # FanDuel format: "119176-52183" -> extract the number after the dash
                    active_player_ids = set()
                    for fd_id in fd_slate['Id'].dropna():
                        if '-' in str(fd_id):
                            player_id = str(fd_id).split('-')[1]
                            active_player_ids.add(player_id)
                logging.info(f"TARGET: Found {len(active_player_ids)} confirmed starters for prop analysis")
            except Exception as e:
                logging.warning(f"ERROR: Could not load confirmed starters: {e}")
        
        feature_files = {
            'hitter': [
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_hitter_features_final.csv",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\hitter_features_today.csv",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\prediction_features_enhanced_real_stats.csv",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\final_prediction_features.csv"
            ],
            'pitcher': [
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\pitcher_features_probables.csv",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_pitcher_features_final.csv",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\pitcher_features_today.csv"
            ]
        }
        
        features = {}
        
        for player_type, file_list in feature_files.items():
            for file_path in file_list:
                if os.path.exists(file_path):
                    try:
                        df = pd.read_csv(file_path, parse_dates=['date'] if 'date' in pd.read_csv(file_path, nrows=1).columns else None)
                        
                        # OPTIMIZATION: Filter to active players only FIRST
                        if active_player_ids:
                            original_count = len(df)
                            # Handle different column names for player ID
                            player_id_col = None
                            for col in ['player_id', 'Id', 'id', 'playerId']:
                                if col in df.columns:
                                    player_id_col = col
                                    break
                            
                            if player_id_col:
                                # Extract player IDs from FanDuel format if needed
                                if player_id_col == 'Id' and df[player_id_col].iloc[0] and '-' in str(df[player_id_col].iloc[0]):
                                    # FanDuel format: "119176-52183" -> extract the number after the dash
                                    df['extracted_id'] = df[player_id_col].astype(str).str.split('-').str[1]
                                    df = df[df['extracted_id'].isin(active_player_ids)]
                                else:
                                    df = df[df[player_id_col].astype(str).isin(active_player_ids)]
                                logging.info(f"TARGET: Filtered {player_type} from {original_count} to {len(df)} active players using {player_id_col}")
                            else:
                                logging.warning(f"WARNING: No player ID column found in {player_type} data")
                        else:
                            logging.warning(f"WARNING: No active player IDs available for filtering")
                        
                        # Additional date filtering for hitters if available
                        if 'date' in df.columns and player_type == 'hitter':
                            target_date = pd.to_datetime(date_str)
                            df_today = df[df['date'] == target_date]
                            if len(df_today) > 0:
                                df = df_today
                                logging.info(f"TARGET: Further filtered {player_type} to {len(df)} players for {date_str}")
                        
                        if len(df) > 0:
                            features[player_type] = df
                            logging.info(f"SUCCESS: Loaded {player_type} features: {len(df)} players from {os.path.basename(file_path)}")
                            break
                        else:
                            logging.warning(f"WARNING: No {player_type} data after filtering from {os.path.basename(file_path)}")
                            
                    except Exception as e:
                        logging.warning(f"ERROR: Error loading {file_path}: {e}")
        
        # Final validation
        total_players = sum(len(df) for df in features.values())
        logging.info(f"TARGET: OPTIMIZATION COMPLETE: Processing {total_players} players instead of 400K+")
        
        return features
    
    def derive_computed_columns(self, df, category):
        """Derive computed columns as in your training scripts"""
        df = df.copy()
        
        if category == "total_bases":
            df['totalBases'] = (
                df.get('hits', 0) + 
                df.get('doubles', 0) * 2 + 
                df.get('triples', 0) * 3 + 
                df.get('homeRuns', 0) * 4
            )
        elif category == "hrr":
            df['hrr'] = (
                df.get('hits', 0) + 
                df.get('runs', 0) + 
                df.get('rbi', 0)
            )
        elif category == "hr_binary":
            df['homeRuns_binary'] = (df.get('homeRuns', 0) > 0).astype(int)
        elif category == "win_binary":
            # Win_binary model - handle missing wins column gracefully
            if 'wins' in df.columns:
                df['win_binary'] = (df['wins'] > 0).astype(int)
            else:
                # Create synthetic win_binary based on available data
                # Use a combination of offensive performance indicators
                df['win_binary'] = ((df.get('homeRuns', 0) + df.get('rbi', 0) + df.get('runs', 0)) > 2).astype(int)
                logging.warning(f"WARNING: Using synthetic win_binary (no wins column available)")
        
        return df
    
    def generate_all_predictions(self, date_str):
        """Generate predictions for all loaded models"""
        logging.info(f"TARGET: Generating predictions for {date_str}...")
        
        features = self.load_today_features(date_str)
        if not features:
            logging.error("ERROR: No feature data loaded")
            return {}
        
        predictions = {}
        
        for category, model_info in self.models.items():
            model = model_info['model']
            player_type = model_info['player_type']
            
            if player_type not in features:
                logging.warning(f"WARNING: No {player_type} features for {category}")
                continue
            
            try:
                df = features[player_type].copy()
                df = self.derive_computed_columns(df, category)
                
                # Prepare features for prediction
                if hasattr(model, 'feature_names_in_'):
                    # XGBoost model from holdout script
                    expected_features = list(model.feature_names_in_)
                else:
                    # Pipeline model - get from preprocessor
                    expected_features = list(model.named_steps['preprocess'].transformers_[0][1].feature_names_in_)
                
                # Select numeric features and align with training
                X = df.select_dtypes(include=[np.number]).copy()
                
                # Add missing features with zeros
                for col in expected_features:
                    if col not in X.columns:
                        X[col] = 0
                
                # Ensure correct column order
                X = X.reindex(columns=expected_features, fill_value=0)
                
                # Generate predictions
                preds = model.predict(X)
                
                # Also get probabilities for classification models
                if model_info['task_type'] == 'classification':
                    try:
                        probs = model.predict_proba(X)[:, 1]  # Probability of positive class
                    except:
                        probs = preds.astype(float) if hasattr(preds, 'astype') else np.array(preds, dtype=float)
                else:
                    probs = None
                
                # Store predictions with player info
                # Handle different player ID column names
                player_id_col = None
                for col in ['player_id', 'Id', 'id', 'playerId', 'extracted_id']:
                    if col in df.columns:
                        player_id_col = col
                        break
                
                if not player_id_col:
                    logging.error(f"ERROR: No player ID column found for {category}")
                    continue
                
                pred_df = df[[player_id_col]].copy()
                pred_df.rename(columns={player_id_col: 'player_id'}, inplace=True)
                
                if 'name' in df.columns:
                    pred_df['name'] = df['name']
                elif 'First Name' in df.columns and 'Last Name' in df.columns:
                    pred_df['name'] = df['First Name'] + ' ' + df['Last Name']
                elif 'player_name' in df.columns:
                    pred_df['name'] = df['player_name']
                else:
                    pred_df['name'] = f"Player_{df[player_id_col]}"
                
                # For pitcher strikeouts, preserve the outs column for role adjustment
                if category == 'pitcher_strikeouts' and 'outs' in df.columns:
                    pred_df['outs'] = df['outs']
                
                pred_df[f'predicted_{category}'] = preds
                if probs is not None:
                    pred_df[f'prob_{category}'] = probs
                
                predictions[category] = pred_df
                logging.info(f"SUCCESS: Generated {category} predictions for {len(pred_df)} players")
                
            except Exception as e:
                logging.error(f"ERROR: Failed to predict {category}: {e}")
        
        self.predictions = predictions
        return predictions
    
    def validate_scraped_data(self, df, source_name):
        """Validate scraped data for obvious issues and flag potential discrepancies"""
        warnings = []
        
        if df is None or len(df) == 0:
            warnings.append(f"ERROR: {source_name}: No data found")
            return warnings
            
        # Check for reasonable line ranges
        if 'line' in df.columns:
            lines = pd.to_numeric(df['line'], errors='coerce')
            if not lines.isna().all():
                # Check for extremely high/low lines that might indicate errors
                high_lines = lines[lines > 20]  # Very high lines might be errors
                low_lines = lines[lines < 0.5]  # Very low lines might be errors
                
                if len(high_lines) > 0:
                    warnings.append(f"WARNING: {source_name}: {len(high_lines)} unusually high lines (>20) found")
                if len(low_lines) > 0:
                    warnings.append(f"WARNING: {source_name}: {len(low_lines)} unusually low lines (<0.5) found")
        
        # Check timestamp freshness (if available)
        current_time = datetime.now()
        
        # Flag specific known issues
        if source_name == "PrizePicks":
            hunter_brown = df[df['player_name'].str.contains('Hunter Brown', case=False, na=False)]
            if len(hunter_brown) > 0:
                for _, row in hunter_brown.iterrows():
                    if 'Pitcher Strikeouts' in df.columns and pd.notna(row.get('Pitcher Strikeouts')):
                        line_value = row.get('Pitcher Strikeouts')
                        if line_value == 8.5:
                            warnings.append(f" KNOWN ISSUE: Hunter Brown strikeouts showing {line_value} - Verify actual line is 7.0 on PrizePicks site")
        
        if warnings:
            for warning in warnings:
                logging.warning(warning)
        else:
            logging.info(f"SUCCESS: {source_name}: Data validation passed")
            
        return warnings

    def load_sportsbook_lines(self):
        """Load lines from all available sportsbooks - now with live scraping!"""
        lines = {}
        data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
        
        # FanDuel (keep existing file-based approach for now)
        fd_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data/fd_slate_starters_only.csv"
        if os.path.exists(fd_file):
            try:
                df = pd.read_csv(fd_file)
                df['source'] = 'FanDuel'
                lines['fanduel'] = df
                logging.info(f"DATA: Loaded FanDuel: {len(df)} props")
            except Exception as e:
                logging.warning(f"ERROR: Error loading FanDuel: {e}")
        
        # PrizePicks - Run the existing scraper script!
        logging.info(" Running PrizePicks scraper...")
        try:
            import subprocess
            # Use the full Python path that works
            python_exe = r"C:\Users\kgone\AppData\Local\Programs\Python\Python311\python.exe"
            script_path = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\PrizePicks_mlb.py"
            
            result = subprocess.run([python_exe, script_path], 
                                  capture_output=True, text=True,
                                  cwd=r"c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts")
            if result.returncode == 0:
                logging.info("SUCCESS: PrizePicks scraper completed successfully")
                logging.info(f"DATA: PrizePicks scraper output: {result.stdout[-500:]}")  # Show last 500 chars
            else:
                logging.warning(f"WARNING: PrizePicks scraper failed: {result.stderr}")
        except Exception as e:
            logging.warning(f"ERROR: Failed to run PrizePicks scraper: {e}")
        
        # Load PrizePicks data (find most recent file)
        try:
            pp_files = [f for f in os.listdir(data_dir) if f.startswith('PP_mlb_picks_') and f.endswith('.xlsx')]
            if pp_files:
                pp_file = max(pp_files, key=lambda x: x)  # Get most recent by filename
                pp_path = os.path.join(data_dir, pp_file)
                df = pd.read_excel(pp_path)
                
                # Validate the raw Excel data
                self.validate_scraped_data(df, "PrizePicks")
                
                # Convert to long format
                df_long = pd.melt(df, id_vars=['player_name'], value_name='line').dropna(subset=['line'])
                df_long['source'] = 'PrizePicks'
                lines['prizepicks'] = df_long
                logging.info(f"DATA: Loaded PrizePicks: {len(df_long)} props from {pp_file}")
        except Exception as e:
            logging.warning(f"ERROR: Error loading PrizePicks: {e}")
        
        # Underdog Fantasy - Load from existing CSV file (run underdog_fantasy_mlb.py manually first)
        logging.info(" Loading Underdog data from CSV...")
        try:
            # Look for today's Underdog CSV file
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Try multiple possible filenames for Underdog data
            ud_files_to_try = [
                f"today_pitcher_props_{today}.csv",
                f"today_pitcher_props_{yesterday}.csv",
                "today_pitcher_props_latest.csv",
                "uf_mlb_picks.csv"
            ]
            
            loaded_ud = False
            for ud_filename in ud_files_to_try:
                ud_file = os.path.join(data_dir, ud_filename)
                if os.path.exists(ud_file):
                    df = pd.read_csv(ud_file)
                    
                    # Validate the CSV data
                    self.validate_scraped_data(df, "Underdog")
                    
                    df['source'] = 'Underdog'
                    lines['underdog'] = df
                    logging.info(f"DATA: Loaded Underdog: {len(df)} props from {ud_filename}")
                    loaded_ud = True
                    break
            
            if not loaded_ud:
                logging.warning("WARNING: No Underdog CSV file found. Run underdog_fantasy_mlb.py manually first.")
                logging.info("Expected files: " + ", ".join(ud_files_to_try))
                
        except Exception as e:
            logging.warning(f"ERROR: Error loading Underdog CSV: {e}")
            logging.warning("WARNING: Run underdog_fantasy_mlb.py manually first to generate the CSV file.")
        
        return lines
    
    def calculate_implied_probability(self, odds, source=None, num_picks=2):
        """
        Convert odds to implied probability, accounting for different sportsbook formats
        
        Args:
            odds: Traditional odds (e.g., -110) or None for fixed payout platforms
            source: Sportsbook source ('prizepicks', 'underdog', etc.)
            num_picks: Number of picks in entry (for PrizePicks/Underdog calculations)
        """
        # Handle PrizePicks and Underdog fixed payout systems
        if source == 'prizepicks':
            # PrizePicks Power Play implied odds per leg
            # Based on their fixed payout multipliers
            payout_odds_map = {
                2: -136.6,  # 3x payout  ~57.7% win rate needed per leg
                3: -141.0,  # 5x payout  ~58.5% win rate needed per leg  
                4: -128.0,  # 10x payout  ~56.1% win rate needed per leg
                5: -122.0,  # 20x payout  ~55.0% win rate needed per leg
                6: -120.0   # 25x payout  ~54.5% win rate needed per leg
            }
            implied_odds = payout_odds_map.get(num_picks, -136.6)  # Default to 2-pick
            return abs(implied_odds) / (abs(implied_odds) + 100)
            
        elif source == 'underdog':
            # Underdog Standard Entry implied odds per leg
            # Generally better payouts than PrizePicks
            payout_odds_map = {
                2: -136.6,  # 3x payout  ~57.7% win rate needed per leg
                3: -122.0,  # 6x payout  ~55.0% win rate needed per leg (better than PP)
                4: -128.0,  # 10x payout  ~56.1% win rate needed per leg
                5: -122.0   # 20x payout  ~55.0% win rate needed per leg
            }
            implied_odds = payout_odds_map.get(num_picks, -136.6)  # Default to 2-pick
            return abs(implied_odds) / (abs(implied_odds) + 100)
        
        # Traditional sportsbook odds (FanDuel, DraftKings, etc.)
        if pd.isna(odds):
            return 0.524  # Default to -110 equivalent (52.4%)
        
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def calculate_expected_value(self, win_probability, implied_probability, bet_amount=1):
        """
        Calculate expected value of a specific bet
        
        Args:
            win_probability: Probability this specific bet wins (model probability)
            implied_probability: Market's implied probability for this bet
            bet_amount: Amount wagered
        """
        # Calculate payout based on implied probability
        payout = bet_amount / implied_probability - bet_amount
        
        # Calculate expected value
        lose_prob = 1 - win_probability
        ev = (win_probability * payout) - (lose_prob * bet_amount)
        return ev
    
    def find_betting_opportunities(self, predictions, lines, min_edge=0.05):
        """Find profitable betting opportunities"""
        opportunities = []
        total_predictions_checked = 0
        total_matches_found = 0
        
        # Stat type mapping
        stat_mapping = {
            'hitter_strikeouts': ['Batter Strikeouts', 'Hitter Strikeouts', 'strikeouts'],  # NEW: Hitter being struck out
            'pitcher_strikeouts': ['Pitcher Strikeouts', 'Strikeouts'],  # Pitcher striking out batters - added "Strikeouts"
            'hits': ['Hits', 'hits'],
            'total_bases': ['Total Bases', 'total_bases'],
            'runs': ['Runs', 'runs'], 
            'rbi': ['RBIs', 'rbi'],
            'home_runs': ['Home Runs', 'home_runs']
        }
        
        for category, pred_df in predictions.items():
            if category not in stat_mapping:
                logging.debug(f" Skipping {category} (not in stat mapping)")
                continue
            
            logging.info(f" Processing {category}: {len(pred_df)} predictions")
            category_matches = 0
                
            stat_names = stat_mapping[category]
            
            # Process in batches for better performance
            for i, (_, pred_row) in enumerate(pred_df.iterrows()):
                if i % 100 == 0 and i > 0:
                    logging.info(f"   Progress: {i}/{len(pred_df)} players processed, {category_matches} matches found")
                
                player_name = pred_row['name']
                prediction = pred_row[f'predicted_{category}']
                
                # Skip if player_name is invalid
                if pd.isna(player_name) or not isinstance(player_name, str) or player_name.strip() == '':
                    continue
                
                # PITCHER ROLE ADJUSTMENT: Apply early before storing prediction
                # The model was trained mostly on relief pitchers but prop lines are typically for starting pitchers
                if category == 'pitcher_strikeouts':
                    pitcher_outs = pred_row.get('outs', 0)
                    
                    # Debug logging
                    if 'Logan Webb' in player_name:
                        logging.info(f" DEBUG Logan Webb: outs={pitcher_outs}, prediction={prediction:.2f}")
                    
                    if pitcher_outs >= 15:  # 5+ innings = starter
                        # Starters average 5.20 K vs model training average of 2.03
                        starter_adjustment = 5.20 / 2.03  # 2.56x multiplier
                        original_pred = prediction
                        prediction = prediction * starter_adjustment
                        logging.info(f"PROGRESS: STARTER ADJUSTMENT: {player_name} prediction adjusted from {original_pred:.2f} to {prediction:.2f} K (outs: {pitcher_outs})")
                    elif pitcher_outs >= 6:  # 2-4 innings = long relief
                        # Long relief average ~2.5 K vs model average of 2.03
                        relief_adjustment = 2.5 / 2.03  # 1.23x multiplier
                        original_pred = prediction
                        prediction = prediction * relief_adjustment
                        logging.info(f"DATA: RELIEF ADJUSTMENT: {player_name} prediction adjusted from {original_pred:.2f} to {prediction:.2f} K (outs: {pitcher_outs})")
                    # Short relief/closers: no adjustment (matches training data)
                
                # Search all sportsbooks for this player/stat combo
                for source, line_df in lines.items():
                    matching_lines = []
                    
                    if source == 'prizepicks':
                        # Skip home runs for PrizePicks since they only offer OVER (no betting value)
                        if category == 'home_runs':
                            logging.debug(f" Skipping {category} for PrizePicks (OVER only)")
                            continue
                            
                        # Match PrizePicks format
                        for stat_name in stat_names:
                            # Ensure player_name is a string and has content
                            if pd.isna(player_name) or not isinstance(player_name, str) or player_name.strip() == '':
                                continue
                                
                            # Safely extract first name
                            try:
                                first_name = player_name.split()[0]
                                if len(first_name) < 2:  # Skip very short names
                                    continue
                                    
                                matches = line_df[
                                    (line_df['player_name'].str.contains(first_name, case=False, na=False, regex=False)) &
                                    (line_df['variable'] == stat_name)
                                ]
                                matching_lines.extend(matches.to_dict('records'))
                            except (IndexError, AttributeError):
                                continue
                    
                    elif source == 'underdog':
                        # Match Underdog format
                        for stat_name in stat_names:
                            # Ensure player_name is a string and has content
                            if pd.isna(player_name) or not isinstance(player_name, str) or player_name.strip() == '':
                                continue
                                
                            # Safely extract first name
                            try:
                                first_name = player_name.split()[0]
                                if len(first_name) < 2:  # Skip very short names
                                    continue
                                    
                                matches = line_df[
                                    (line_df['player_name'].str.contains(first_name, case=False, na=False, regex=False)) &
                                    (line_df['stat_type'] == stat_name)
                                ]
                                matching_lines.extend(matches.to_dict('records'))
                            except (IndexError, AttributeError):
                                continue
                    
                    # Calculate EV for each matching line
                    for line_row in matching_lines:
                        line_value = line_row['line']
                        
                        # Calculate model probability vs line
                        if self.models[category]['task_type'] == 'regression':
                            # Validate prediction first - skip if unrealistic
                            if prediction < 0 or prediction > 50:  # Reasonable upper bound for baseball stats
                                logging.warning(f"WARNING: Skipping unrealistic prediction for {player_name} {category}: {prediction}")
                                continue
                            
                            # Use normal distribution assumption with VALIDATED standard deviations
                            # Based on validation RMSE data from model training
                            if category in ['pitcher_strikeouts', 'hitter_strikeouts']:
                                std_dev = 1.461  # Use actual RMSE from validation data
                            elif category in ['hits', 'runs', 'rbi']:
                                std_dev = max(1.0, prediction * 0.4)  # 40% of prediction, min 1.0
                            elif category == 'total_bases':
                                std_dev = max(1.5, prediction * 0.35)  # 35% of prediction, min 1.5
                            elif category == 'home_runs':
                                std_dev = max(0.5, prediction * 0.5)  # 50% of prediction, min 0.5
                            else:
                                std_dev = max(1.0, prediction * 0.3)  # Default: 30% of prediction, min 1.0
                            
                            model_prob_over = 1 - stats.norm.cdf(line_value, loc=prediction, scale=std_dev)
                            
                            # Ensure probabilities are reasonable (between 0.01 and 0.99)
                            model_prob_over = max(0.01, min(0.99, model_prob_over))
                        else:
                            # Use classification probability if available
                            model_prob_over = pred_row.get(f'prob_{category}', 0.5)
                        
                        # Calculate EV for each matching line across multiple entry types
                        best_opportunities = []
                        
                        # For PrizePicks/Underdog, test different entry sizes (2-6 picks)
                        if source in ['prizepicks', 'underdog']:
                            entry_sizes = [2, 3, 4, 5] if source == 'underdog' else [2, 3, 4, 5, 6]
                            for num_picks in entry_sizes:
                                implied_prob = self.calculate_implied_probability(None, source, num_picks)
                                
                                # Calculate EV for both OVER and UNDER
                                ev_over = self.calculate_expected_value(model_prob_over, implied_prob)
                                ev_under = self.calculate_expected_value(1 - model_prob_over, 1 - implied_prob)
                                
                                # Store best bet for this entry size
                                if ev_over > ev_under and ev_over > min_edge:
                                    best_opportunities.append({
                                        'ev': ev_over,
                                        'bet_type': 'OVER',
                                        'entry_size': num_picks,
                                        'implied_prob': implied_prob
                                    })
                                elif ev_under > min_edge:
                                    best_opportunities.append({
                                        'ev': ev_under,
                                        'bet_type': 'UNDER', 
                                        'entry_size': num_picks,
                                        'implied_prob': implied_prob
                                    })
                        else:
                            # Traditional sportsbook - single calculation
                            odds = line_row.get('odds', -110)
                            implied_prob = self.calculate_implied_probability(odds)
                            ev_over = self.calculate_expected_value(model_prob_over, implied_prob)
                            ev_under = self.calculate_expected_value(1 - model_prob_over, 1 - implied_prob)
                            
                            if ev_over > ev_under and ev_over > min_edge:
                                best_opportunities.append({
                                    'ev': ev_over,
                                    'bet_type': 'OVER',
                                    'entry_size': 1,
                                    'implied_prob': implied_prob
                                })
                            elif ev_under > min_edge:
                                best_opportunities.append({
                                    'ev': ev_under,
                                    'bet_type': 'UNDER',
                                    'entry_size': 1,
                                    'implied_prob': implied_prob
                                })
                        
                        # Add the best opportunity for this line
                        if best_opportunities:
                            best_opp = max(best_opportunities, key=lambda x: x['ev'])
                            
                            # Calculate Kelly bet sizing
                            win_prob = model_prob_over if best_opp['bet_type'] == 'OVER' else (1 - model_prob_over)
                            kelly_bet_size = self.calculate_kelly_bet_size(best_opp['ev'], win_prob)
                            
                            opportunities.append({
                                'player': player_name,
                                'category': category,
                                'source': source,
                                'line': line_value,
                                'prediction': prediction,
                                'model_prob_over': model_prob_over,
                                'implied_prob': best_opp['implied_prob'],
                                'recommended_bet': best_opp['bet_type'],
                                'expected_value': best_opp['ev'],
                                'edge': best_opp['ev'],
                                'confidence': self._get_confidence_level(best_opp['ev']),
                                'optimal_entry_size': best_opp['entry_size'],
                                'kelly_bet_pct': kelly_bet_size / 1000,  # As percentage of bankroll
                                'kelly_bet_amount': kelly_bet_size,  # Dollar amount for $1000 bankroll
                                'odds': f"{best_opp['entry_size']}-pick entry (~{best_opp['implied_prob']:.1%} per leg)" if source in ['prizepicks', 'underdog'] else line_row.get('odds', -110)
                            })
                            category_matches += 1
            
            logging.info(f"SUCCESS: {category}: {category_matches} matches found")
            total_matches_found += category_matches
        
        logging.info(f"DATA: Total opportunities found: {len(opportunities)} from {total_matches_found} matches")
        return sorted(opportunities, key=lambda x: x['edge'], reverse=True)
    
    def build_optimal_combinations(self, opportunities, target_sizes=[3, 4, 5]):
        """
        Build optimal prop combinations for multi-pick entries
        FIXED: Removed 6-pick to prevent system hang (15M+ combinations)
        
        Args:
            opportunities: List of individual betting opportunities
            target_sizes: List of combination sizes to build (e.g., [3, 4, 5])
        """
        from itertools import combinations
        import numpy as np
        
        # Filter high-quality opportunities for combinations
        quality_opps = [opp for opp in opportunities if opp['edge'] >= 0.08 and opp['kelly_bet_pct'] >= 0.02]
        
        print(f" Building combinations from {len(quality_opps)} quality opportunities...")
        
        optimal_combinations = []
        
        for size in target_sizes:
            print(f"DATA: Analyzing {size}-pick combinations...")
            
            # Generate all possible combinations of this size
            best_combos = []
            
            # FIXED: Reduce from 50 to 20 to prevent hangs (C(20,5) = 15,504 vs C(50,6) = 15M+)
            max_players = min(20, len(quality_opps))
            for combo in combinations(quality_opps[:max_players], size):
                # Calculate combination metrics
                total_ev = sum(opp['expected_value'] for opp in combo)
                avg_edge = total_ev / size
                
                # Check for correlation issues (same player, same game, etc.)
                players = [opp['player'] for opp in combo]
                categories = [opp['category'] for opp in combo]
                
                # Avoid same player multiple times
                if len(set(players)) < len(players):
                    continue
                
                # Prefer diverse stat categories
                category_diversity = len(set(categories)) / len(categories)
                
                # Calculate combined Kelly sizing (conservative for combinations)
                kelly_sizes = [opp['kelly_bet_pct'] for opp in combo]
                combined_kelly = min(0.15, sum(kelly_sizes) * 0.6)  # 60% of sum, max 15%
                
                # Calculate win probability (assuming independence)
                win_probs = []
                for opp in combo:
                    if opp['recommended_bet'] == 'OVER':
                        win_probs.append(opp['model_prob_over'])
                    else:
                        win_probs.append(1 - opp['model_prob_over'])
                
                combined_win_prob = np.prod(win_probs)
                
                # Score this combination
                diversity_bonus = category_diversity * 0.1
                combo_score = avg_edge + diversity_bonus
                
                # Create detailed summary with stat types and lines
                detailed_picks = []
                for opp in combo:
                    pick_detail = f"{opp['player']} {opp['category']} {opp['recommended_bet']} {opp['line']}"
                    detailed_picks.append(pick_detail)
                
                best_combos.append({
                    'size': size,
                    'picks': combo,
                    'total_ev': total_ev,
                    'avg_edge': avg_edge,
                    'combined_kelly': combined_kelly,
                    'win_probability': combined_win_prob,
                    'category_diversity': category_diversity,
                    'score': combo_score,
                    'players': players,
                    'summary': f"{size}-pick: " + ', '.join([f"{opp['player']} {opp['recommended_bet']}" for opp in combo]),
                    'detailed_summary': f"{size}-pick: " + ' | '.join(detailed_picks),
                    'pick_details': [
                        {
                            'player': opp['player'],
                            'stat': opp['category'],
                            'line': opp['line'],
                            'bet': opp['recommended_bet'],
                            'prediction': opp['prediction'],
                            'source': opp['source'],
                            'edge': opp['edge']
                        } for opp in combo
                    ]
                })
            
            # Keep top 5 combinations for this size
            best_combos.sort(key=lambda x: x['score'], reverse=True)
            optimal_combinations.extend(best_combos[:5])
            
            if best_combos:
                print(f"SUCCESS: Best {size}-pick combo: {best_combos[0]['avg_edge']:.1%} avg edge, {best_combos[0]['win_probability']:.1%} win prob")
        
        return sorted(optimal_combinations, key=lambda x: x['score'], reverse=True)

    def calculate_kelly_bet_size(self, edge, win_probability, bankroll=1000):
        """
        Calculate optimal bet size using Kelly Criterion
        
        Args:
            edge: Expected value as decimal (e.g., 0.15 for 15% edge)
            win_probability: Probability of winning the bet
            bankroll: Total bankroll available
        """
        if win_probability <= 0 or win_probability >= 1:
            return 0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds, p = win prob, q = lose prob
        lose_probability = 1 - win_probability
        
        # Convert edge to odds: if edge = 0.15, then odds = 1.15
        odds_decimal = 1 + edge
        
        # Kelly fraction
        kelly_fraction = (odds_decimal * win_probability - lose_probability) / odds_decimal
        
        # Cap at 25% of bankroll for safety (fractional Kelly)
        kelly_fraction = max(0, min(0.25, kelly_fraction))
        
        return kelly_fraction * bankroll

    def _get_confidence_level(self, edge):
        """Determine confidence level based on edge size"""
        if edge >= 0.20:
            return 'VERY_HIGH'
        elif edge >= 0.15:
            return 'HIGH'
        elif edge >= 0.10:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_betting_report(self, opportunities, output_dir):
        """Generate comprehensive betting report"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not opportunities:
            logging.warning("WARNING: No betting opportunities found")
            return
        
        # Save detailed CSV
        df = pd.DataFrame(opportunities)
        csv_file = f"{output_dir}/betting_opportunities_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # Generate summary report
        report_file = f"{output_dir}/betting_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("TARGET: AUTOMATED BETTING SYSTEM REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Top opportunities
            f.write("LINEUP: TOP 10 BETTING OPPORTUNITIES:\n")
            f.write("-"*80 + "\n")
            
            for i, opp in enumerate(opportunities[:10], 1):
                f.write(f"{i:2d}. {opp['player']:25s} | {opp['category']:12s} | {opp['source']:10s}\n")
                f.write(f"    Line: {opp['line']:5.1f} | Prediction: {opp['prediction']:5.1f} | Bet: {opp['recommended_bet']:5s}\n")
                f.write(f"    Edge: {opp['edge']:6.2%} | EV: ${opp['expected_value']:+6.2f} | Confidence: {opp['confidence']}\n")
                f.write(f"    Model Prob: {opp['model_prob_over']:5.1%} | Implied Prob: {opp['implied_prob']:5.1%}\n\n")
            
            # Summary statistics
            by_confidence = df.groupby('confidence').size()
            by_category = df.groupby('category').size()
            by_source = df.groupby('source').size()
            
            f.write("DATA: SUMMARY STATISTICS:\n")
            f.write("-"*40 + "\n")
            f.write(f"Total Opportunities: {len(opportunities)}\n")
            f.write(f"Average Edge: {df['edge'].mean():.2%}\n")
            f.write(f"Total Expected Value: ${df['expected_value'].sum():.2f}\n\n")
            
            f.write("By Confidence Level:\n")
            for conf, count in by_confidence.items():
                f.write(f"  {conf}: {count}\n")
            
            f.write(f"\nBy Category:\n")
            for cat, count in by_category.items():
                f.write(f"  {cat}: {count}\n")
            
            f.write(f"\nBy Sportsbook:\n")
            for source, count in by_source.items():
                f.write(f"  {source}: {count}\n")
        
        logging.info(f"SUCCESS: Betting report saved: {report_file}")
        logging.info(f"SUCCESS: Detailed CSV saved: {csv_file}")
        
        return report_file, csv_file
    
    def run_daily_analysis(self, date_str, min_edge=0.05, output_dir="./betting_analysis"):
        """Run complete daily betting analysis"""
        logging.info(f"START: Starting automated betting analysis for {date_str}")
        
        # Load models
        if not self.load_all_models():
            logging.error("ERROR: No models loaded - run training first!")
            return False
        
        # Generate predictions
        predictions = self.generate_all_predictions(date_str)
        if not predictions:
            logging.error("ERROR: No predictions generated")
            return False
        
        # Load sportsbook lines
        lines = self.load_sportsbook_lines()
        if not lines:
            logging.error("ERROR: No sportsbook lines loaded")
            return False
        
        # Find opportunities
        opportunities = self.find_betting_opportunities(predictions, lines, min_edge)
        
        # Generate report
        if opportunities:
            # Build optimal combinations for multi-pick entries
            print("\nTARGET: BUILDING OPTIMAL PROP COMBINATIONS...")
            combinations = self.build_optimal_combinations(opportunities)
            
            # Save combination report
            if combinations:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                combo_file = f"{output_dir}/optimal_combinations_{timestamp}.txt"
                combo_csv = f"{output_dir}/optimal_combinations_{timestamp}.csv"
                
                # Save TXT report
                with open(combo_file, 'w', encoding='utf-8') as f:
                    f.write("TARGET: OPTIMAL PROP COMBINATIONS REPORT\n")
                    f.write("="*80 + "\n\n")
                    
                    for i, combo in enumerate(combinations[:15], 1):
                        f.write(f"{i:2d}. {combo['summary']}\n")
                        f.write(f"    Size: {combo['size']} picks | Avg Edge: {combo['avg_edge']:.1%} | Win Prob: {combo['win_probability']:.1%}\n")
                        f.write(f"    Total EV: {combo['total_ev']:.2f} | Kelly: {combo['combined_kelly']:.1%} | Diversity: {combo['category_diversity']:.1%}\n\n")
                
                # Save CSV version with detailed prop information
                combo_data = []
                for i, combo in enumerate(combinations[:15], 1):
                    # Create detailed breakdown for each pick in the combo
                    pick_details = []
                    for j, pick in enumerate(combo['pick_details'], 1):
                        pick_details.append(f"Pick {j}: {pick['player']} {pick['stat']} {pick['bet']} {pick['line']} (pred: {pick['prediction']:.1f}, edge: {pick['edge']:.1%}, {pick['source']})")
                    
                    combo_data.append({
                        'rank': i,
                        'combo_size': combo['size'],
                        'detailed_combo': combo['detailed_summary'],
                        'pick_1_player': combo['pick_details'][0]['player'] if len(combo['pick_details']) > 0 else '',
                        'pick_1_stat': combo['pick_details'][0]['stat'] if len(combo['pick_details']) > 0 else '',
                        'pick_1_line': combo['pick_details'][0]['line'] if len(combo['pick_details']) > 0 else '',
                        'pick_1_bet': combo['pick_details'][0]['bet'] if len(combo['pick_details']) > 0 else '',
                        'pick_1_prediction': f"{combo['pick_details'][0]['prediction']:.1f}" if len(combo['pick_details']) > 0 else '',
                        'pick_1_source': combo['pick_details'][0]['source'] if len(combo['pick_details']) > 0 else '',
                        'pick_1_edge': f"{combo['pick_details'][0]['edge']:.1%}" if len(combo['pick_details']) > 0 else '',
                        'pick_1_confidence': 'High' if len(combo['pick_details']) > 0 and abs(combo['pick_details'][0]['edge']) > 0.2 else 'Medium' if len(combo['pick_details']) > 0 and abs(combo['pick_details'][0]['edge']) > 0.1 else 'Low' if len(combo['pick_details']) > 0 else '',
                        'pick_2_player': combo['pick_details'][1]['player'] if len(combo['pick_details']) > 1 else '',
                        'pick_2_stat': combo['pick_details'][1]['stat'] if len(combo['pick_details']) > 1 else '',
                        'pick_2_line': combo['pick_details'][1]['line'] if len(combo['pick_details']) > 1 else '',
                        'pick_2_bet': combo['pick_details'][1]['bet'] if len(combo['pick_details']) > 1 else '',
                        'pick_2_prediction': f"{combo['pick_details'][1]['prediction']:.1f}" if len(combo['pick_details']) > 1 else '',
                        'pick_2_source': combo['pick_details'][1]['source'] if len(combo['pick_details']) > 1 else '',
                        'pick_2_edge': f"{combo['pick_details'][1]['edge']:.1%}" if len(combo['pick_details']) > 1 else '',
                        'pick_2_confidence': 'High' if len(combo['pick_details']) > 1 and abs(combo['pick_details'][1]['edge']) > 0.2 else 'Medium' if len(combo['pick_details']) > 1 and abs(combo['pick_details'][1]['edge']) > 0.1 else 'Low' if len(combo['pick_details']) > 1 else '',
                        'pick_3_player': combo['pick_details'][2]['player'] if len(combo['pick_details']) > 2 else '',
                        'pick_3_stat': combo['pick_details'][2]['stat'] if len(combo['pick_details']) > 2 else '',
                        'pick_3_line': combo['pick_details'][2]['line'] if len(combo['pick_details']) > 2 else '',
                        'pick_3_bet': combo['pick_details'][2]['bet'] if len(combo['pick_details']) > 2 else '',
                        'pick_3_prediction': f"{combo['pick_details'][2]['prediction']:.1f}" if len(combo['pick_details']) > 2 else '',
                        'pick_3_source': combo['pick_details'][2]['source'] if len(combo['pick_details']) > 2 else '',
                        'pick_3_edge': f"{combo['pick_details'][2]['edge']:.1%}" if len(combo['pick_details']) > 2 else '',
                        'pick_3_confidence': 'High' if len(combo['pick_details']) > 2 and abs(combo['pick_details'][2]['edge']) > 0.2 else 'Medium' if len(combo['pick_details']) > 2 and abs(combo['pick_details'][2]['edge']) > 0.1 else 'Low' if len(combo['pick_details']) > 2 else '',
                        'pick_4_player': combo['pick_details'][3]['player'] if len(combo['pick_details']) > 3 else '',
                        'pick_4_stat': combo['pick_details'][3]['stat'] if len(combo['pick_details']) > 3 else '',
                        'pick_4_line': combo['pick_details'][3]['line'] if len(combo['pick_details']) > 3 else '',
                        'pick_4_bet': combo['pick_details'][3]['bet'] if len(combo['pick_details']) > 3 else '',
                        'pick_4_prediction': f"{combo['pick_details'][3]['prediction']:.1f}" if len(combo['pick_details']) > 3 else '',
                        'pick_4_source': combo['pick_details'][3]['source'] if len(combo['pick_details']) > 3 else '',
                        'pick_4_edge': f"{combo['pick_details'][3]['edge']:.1%}" if len(combo['pick_details']) > 3 else '',
                        'pick_4_confidence': 'High' if len(combo['pick_details']) > 3 and abs(combo['pick_details'][3]['edge']) > 0.2 else 'Medium' if len(combo['pick_details']) > 3 and abs(combo['pick_details'][3]['edge']) > 0.1 else 'Low' if len(combo['pick_details']) > 3 else '',
                        'pick_5_player': combo['pick_details'][4]['player'] if len(combo['pick_details']) > 4 else '',
                        'pick_5_stat': combo['pick_details'][4]['stat'] if len(combo['pick_details']) > 4 else '',
                        'pick_5_line': combo['pick_details'][4]['line'] if len(combo['pick_details']) > 4 else '',
                        'pick_5_bet': combo['pick_details'][4]['bet'] if len(combo['pick_details']) > 4 else '',
                        'pick_5_prediction': f"{combo['pick_details'][4]['prediction']:.1f}" if len(combo['pick_details']) > 4 else '',
                        'pick_5_source': combo['pick_details'][4]['source'] if len(combo['pick_details']) > 4 else '',
                        'pick_5_edge': f"{combo['pick_details'][4]['edge']:.1%}" if len(combo['pick_details']) > 4 else '',
                        'pick_5_confidence': 'High' if len(combo['pick_details']) > 4 and abs(combo['pick_details'][4]['edge']) > 0.2 else 'Medium' if len(combo['pick_details']) > 4 and abs(combo['pick_details'][4]['edge']) > 0.1 else 'Low' if len(combo['pick_details']) > 4 else '',
                        'avg_edge_pct': f"{combo['avg_edge']:.1%}",
                        'win_probability_pct': f"{combo['win_probability']:.1%}",
                        'total_ev': f"{combo['total_ev']:.2f}",
                        'kelly_bet_pct': f"{combo['combined_kelly']:.1%}",
                        'diversity_pct': f"{combo['category_diversity']:.1%}",
                        'model_confidence': 'Very High' if combo['win_probability'] > 0.9 else 'High' if combo['win_probability'] > 0.75 else 'Medium' if combo['win_probability'] > 0.6 else 'Low',
                        'recommendation': 'STRONG BET' if combo['avg_edge'] > 0.3 and combo['win_probability'] > 0.8 else 'GOOD BET' if combo['avg_edge'] > 0.2 and combo['win_probability'] > 0.7 else 'CONSIDER' if combo['avg_edge'] > 0.15 else 'AVOID',
                        'data_validation_warning': 'WARNING: Verify lines on live platforms - scraped data may be outdated',
                        'all_picks_summary': ' | '.join(pick_details)
                    })
                
                combo_df = pd.DataFrame(combo_data)
                combo_df.to_csv(combo_csv, index=False)
                
                # Also save to data directory for easy access
                data_combo_csv = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\optimal_combinations_today.csv"
                combo_df.to_csv(data_combo_csv, index=False)
                
                print(f"SUCCESS: Optimal combinations saved: {combo_file}")
                print(f"SUCCESS: CSV combinations saved: {combo_csv}")
                print(f"SUCCESS: Easy access copy saved: ../data/optimal_combinations_today.csv")
                print(f"LINEUP: Best combination: {combinations[0]['summary']}")
                print(f"   DATA: {combinations[0]['avg_edge']:.1%} avg edge, {combinations[0]['win_probability']:.1%} win probability")
            
            self.generate_betting_report(opportunities, output_dir)
            logging.info(f"TARGET: Found {len(opportunities)} betting opportunities!")
        else:
            logging.info(" No profitable opportunities found today")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Automated MLB betting system")
    parser.add_argument("--date", default=datetime.now().strftime('%Y-%m-%d'), 
                        help="Date for analysis (YYYY-MM-DD)")
    parser.add_argument("--min-edge", type=float, default=0.05, 
                        help="Minimum edge threshold (default: 5%)")
    parser.add_argument("--models-dir", default="./models", 
                        help="Directory containing trained models")
    parser.add_argument("--output-dir", default="./betting_analysis", 
                        help="Output directory for reports")
    
    args = parser.parse_args()
    
    system = AutomatedBettingSystem(args.models_dir)
    success = system.run_daily_analysis(
        date_str=args.date,
        min_edge=args.min_edge,
        output_dir=args.output_dir
    )
    
    if success:
        logging.info("SUCCESS: Analysis complete!")
    else:
        logging.error("ERROR: Analysis failed!")

if __name__ == "__main__":
    main()

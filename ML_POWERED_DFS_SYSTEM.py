#!/usr/bin/env python3
"""
ML-POWERED DFS OPTIMIZATION SYSTEM
==================================
Integrates your advanced ML prop models into DFS lineup optimization.
Uses the same XGBoost/ensemble models from prop betting for accurate projections.

Features:
- ML-based FPPG projections (not salary-based estimates)
- Uses your trained prop models (hits, HR, RBI, runs, etc.)
- Converts prop predictions to fantasy points
- Enhanced optimization with real ML predictions
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import logging
import joblib
import os
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent / "data"
SCRIPTS_DIR = Path(__file__).resolve().parent
MODELS_DIR = SCRIPTS_DIR / "models"
FD_SLATE_DIR = Path(__file__).resolve().parent.parent / "fd_current_slate"

# Input files
SLATE_FILE = FD_SLATE_DIR / "fd_slate_today.csv"
HITTER_FEATURES = BASE_DIR / "fd_hitter_features_final.csv" 
PITCHER_FEATURES = BASE_DIR / "fd_pitcher_features_final.csv"

# Output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_LINEUPS = BASE_DIR / f"ml_dfs_lineups_{TIMESTAMP}.csv"
OUTPUT_SUMMARY = BASE_DIR / f"ml_dfs_summary_{TIMESTAMP}.csv" 
OUTPUT_FANDUEL = BASE_DIR / f"ml_fanduel_submission_{TIMESTAMP}.csv"

# FanDuel scoring system
FANDUEL_SCORING = {
    'single': 3,
    'double': 6, 
    'triple': 9,
    'home_run': 12,
    'rbi': 3.5,
    'run': 3.2,
    'walk': 3,
    'hit_by_pitch': 3,
    'stolen_base': 6
}

# Pitcher scoring
PITCHER_SCORING = {
    'win': 12,
    'quality_start': 4,  # 6+ IP, 3 or fewer ER
    'inning_pitched': 2.25,
    'strikeout': 3,
    'earned_run': -3,
    'hit_allowed': -0.6,
    'walk_allowed': -0.6,
    'complete_game': 2.5,
    'shutout': 2.5,
    'no_hitter': 5
}

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / f'ml_dfs_optimization_{TIMESTAMP}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# ML MODEL INTEGRATION
# =============================================================================
class MLProjectionEngine:
    """Uses your trained ML models to generate DFS projections"""
    
    def __init__(self):
        self.hitter_models = {}
        self.pitcher_models = {}
        self.load_models()
    
    def load_models(self):
        """Load all trained ML models"""
        logger.info("Loading ML models for DFS projections...")
        
        # Hitter models
        hitter_props = ['hits', 'home_runs', 'rbi', 'runs', 'total_bases', 'stolen_bases']
        for prop in hitter_props:
            model_path = MODELS_DIR / prop / f"{prop}_pipeline.joblib"
            if model_path.exists():
                try:
                    self.hitter_models[prop] = joblib.load(model_path)
                    logger.info(f"✅ Loaded {prop} model")
                except Exception as e:
                    logger.warning(f"❌ Failed to load {prop} model: {e}")
        
        # Pitcher models  
        pitcher_props = ['strikeouts', 'outs', 'win_binary']
        for prop in pitcher_props:
            model_path = MODELS_DIR / prop / f"{prop}_pipeline.joblib"
            if model_path.exists():
                try:
                    self.pitcher_models[prop] = joblib.load(model_path)
                    logger.info(f"✅ Loaded {prop} model")
                except Exception as e:
                    logger.warning(f"❌ Failed to load {prop} model: {e}")
        
        logger.info(f"Loaded {len(self.hitter_models)} hitter models, {len(self.pitcher_models)} pitcher models")
    
    def predict_hitter_fppg(self, features_df):
        """Generate ML-based FPPG projections for hitters"""
        logger.info(f"Generating ML projections for {len(features_df)} hitters...")
        
        predictions = {}
        
        # Get predictions from each model
        for prop, model in self.hitter_models.items():
            try:
                # Prepare features (remove non-numeric columns)
                X = features_df.select_dtypes(include=[np.number]).fillna(0)
                
                # Align features with model expectations
                if hasattr(model, 'feature_names_in_'):
                    expected_features = model.feature_names_in_
                    # Add missing features as zeros
                    for feat in expected_features:
                        if feat not in X.columns:
                            X[feat] = 0
                    # Select only expected features
                    X = X[expected_features]
                
                pred = model.predict(X)
                predictions[prop] = pred
                logger.info(f"Generated {prop} predictions")
                
            except Exception as e:
                logger.warning(f"Failed to predict {prop}: {e}")
                predictions[prop] = np.zeros(len(features_df))
        
        # Convert predictions to fantasy points
        fppg_projections = self.convert_to_fppg(predictions, 'hitter')
        
        return fppg_projections
    
    def predict_pitcher_fppg(self, features_df):
        """Generate ML-based FPPG projections for pitchers"""
        logger.info(f"Generating ML projections for {len(features_df)} pitchers...")
        
        predictions = {}
        
        # Get predictions from each model
        for prop, model in self.pitcher_models.items():
            try:
                # Prepare features
                X = features_df.select_dtypes(include=[np.number]).fillna(0)
                
                # Align features with model expectations
                if hasattr(model, 'feature_names_in_'):
                    expected_features = model.feature_names_in_
                    for feat in expected_features:
                        if feat not in X.columns:
                            X[feat] = 0
                    X = X[expected_features]
                
                pred = model.predict(X)
                predictions[prop] = pred
                logger.info(f"Generated {prop} predictions")
                
            except Exception as e:
                logger.warning(f"Failed to predict {prop}: {e}")
                predictions[prop] = np.zeros(len(features_df))
        
        # Convert predictions to fantasy points
        fppg_projections = self.convert_to_fppg(predictions, 'pitcher')
        
        return fppg_projections
    
    def convert_to_fppg(self, predictions, player_type):
        """Convert ML predictions to FanDuel fantasy points"""
        
        if player_type == 'hitter':
            # Hitter scoring conversion
            fppg = np.zeros(len(next(iter(predictions.values()))))
            
            if 'hits' in predictions:
                # Estimate hit types (simplified)
                hits = predictions['hits']
                singles = hits * 0.7  # ~70% of hits are singles
                fppg += singles * FANDUEL_SCORING['single']
            
            if 'home_runs' in predictions:
                fppg += predictions['home_runs'] * FANDUEL_SCORING['home_run']
            
            if 'rbi' in predictions:
                fppg += predictions['rbi'] * FANDUEL_SCORING['rbi']
            
            if 'runs' in predictions:
                fppg += predictions['runs'] * FANDUEL_SCORING['run']
            
            if 'stolen_bases' in predictions:
                fppg += predictions['stolen_bases'] * FANDUEL_SCORING['stolen_base']
            
            # Add estimated walks (simplified)
            fppg += 0.5 * FANDUEL_SCORING['walk']  # Estimate ~0.5 walks per game
            
        else:  # pitcher
            # Pitcher scoring conversion
            fppg = np.zeros(len(next(iter(predictions.values()))))
            
            if 'strikeouts' in predictions:
                fppg += predictions['strikeouts'] * PITCHER_SCORING['strikeout']
            
            if 'outs' in predictions:
                # Convert outs to innings (3 outs = 1 inning)
                innings = predictions['outs'] / 3
                fppg += innings * PITCHER_SCORING['inning_pitched']
            
            if 'win_binary' in predictions:
                # Win probability
                fppg += predictions['win_binary'] * PITCHER_SCORING['win']
            
            # Add baseline quality start bonus (simplified)
            fppg += 2  # Average quality start component
            
            # Subtract average hits/walks allowed (simplified)
            fppg -= 4 * PITCHER_SCORING['hit_allowed']  # ~4 hits allowed
            fppg -= 2 * PITCHER_SCORING['walk_allowed']  # ~2 walks allowed
        
        return fppg

# =============================================================================
# ENHANCED DFS OPTIMIZATION
# =============================================================================
def load_and_project_players():
    """Load players and generate ML-based projections"""
    logger.info("Loading player data and generating ML projections...")
    
    # Load slate
    slate = pd.read_csv(SLATE_FILE)
    logger.info(f"Loaded {len(slate)} players from slate")
    
    # Filter for active players (exclude those with Batting Order = '0')
    # BUT keep starting pitchers (Probable Pitcher = 'Yes') regardless of batting order
    if 'Batting Order' in slate.columns:
        initial_count = len(slate)
        # Convert to string and handle various "0" representations
        slate['Batting Order'] = slate['Batting Order'].astype(str).str.strip()
        
        # Keep starting pitchers regardless of batting order
        starting_pitchers = slate[(slate['Position'] == 'P') & (slate['Probable Pitcher'] == 'Yes')]
        
        # Keep non-pitchers who have valid batting orders (not "0")
        active_non_pitchers = slate[
            (slate['Position'] != 'P') & 
            (~slate['Batting Order'].isin(['0', '0.0', 'nan', '']))
        ]
        
        # Combine active players
        slate = pd.concat([starting_pitchers, active_non_pitchers], ignore_index=True)
        filtered_count = len(slate)
        logger.info(f"After filtering out inactive players: {filtered_count} players (removed {initial_count - filtered_count})")
        logger.info(f"Kept {len(starting_pitchers)} starting pitchers and {len(active_non_pitchers)} active non-pitchers")
    
    # Extract player_id from FanDuel format
    if 'Id' in slate.columns:
        slate['player_id'] = slate['Id'].astype(str).str.split('-').str[1]
    
    # Standardize columns
    slate['salary'] = slate.get('Salary', slate.get('salary', 0)).astype(int)
    slate['position'] = slate.get('Position', slate.get('position', ''))
    slate['name'] = slate.get('Nickname', slate.get('Name', 'Unknown'))
    slate['team'] = slate.get('Team', slate.get('team', ''))
    
    # Load features
    hitters = pd.DataFrame()
    pitchers = pd.DataFrame()
    
    if Path(HITTER_FEATURES).exists():
        hitters = pd.read_csv(HITTER_FEATURES)
        hitters['player_id'] = hitters['player_id'].astype(str)
    
    if Path(PITCHER_FEATURES).exists():
        pitchers = pd.read_csv(PITCHER_FEATURES)  
        pitchers['player_id'] = pitchers['player_id'].astype(str)
    
    # Initialize ML projection engine
    ml_engine = MLProjectionEngine()
    
    # Generate projections
    all_players = []
    
    for _, player in slate.iterrows():
        player_id = str(player['player_id'])
        
        # Check if pitcher
        if 'P' in player['position']:
            # Find pitcher features
            pitcher_features = pitchers[pitchers['player_id'] == player_id]
            if len(pitcher_features) > 0:
                ml_fppg = ml_engine.predict_pitcher_fppg(pitcher_features)
                projected_fppg = ml_fppg[0] if len(ml_fppg) > 0 else 15.0
            else:
                projected_fppg = player['salary'] / 1000 * 1.5  # Fallback
        else:
            # Find hitter features
            hitter_features = hitters[hitters['player_id'] == player_id]
            if len(hitter_features) > 0:
                ml_fppg = ml_engine.predict_hitter_fppg(hitter_features)
                projected_fppg = ml_fppg[0] if len(ml_fppg) > 0 else 8.0
            else:
                projected_fppg = player['salary'] / 1000 * 2.5  # Fallback
        
        # Create player record
        player_data = {
            'player_id': player_id,
            'name': player['name'],
            'position': player['position'],
            'primary_position': player['position'].split('/')[0],
            'team': player['team'],
            'salary': player['salary'],
            'ml_projected_fppg': projected_fppg,
            'ceiling_fppg': projected_fppg * 1.4,
            'floor_fppg': projected_fppg * 0.7,
            'value_score': projected_fppg / (player['salary'] / 1000)
        }
        all_players.append(player_data)
    
    return pd.DataFrame(all_players)

def optimize_ml_lineups(df):
    """Generate optimized lineups using ML projections"""
    logger.info("Optimizing lineups with ML projections...")
    
    strategies = {
        'floor': {'count': 3, 'ceiling_weight': 0.1, 'floor_weight': 0.6, 'value_weight': 0.3},
        'balanced': {'count': 14, 'ceiling_weight': 0.3, 'floor_weight': 0.3, 'value_weight': 0.4},
        'ceiling': {'count': 3, 'ceiling_weight': 0.7, 'floor_weight': 0.1, 'value_weight': 0.2}
    }
    
    position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    salary_cap = 35000
    
    all_lineups = []
    lineup_id = 1
    
    for strategy, config in strategies.items():
        logger.info(f"Generating {config['count']} {strategy} lineups...")
        
        for i in range(config['count']):
            # Create optimization problem
            prob = LpProblem(f"ML_DFS_{strategy}_{i}", LpMaximize)
            
            # Decision variables
            player_vars = {idx: LpVariable(f"player_{idx}", cat='Binary') for idx in df.index}
            
            # Calculate composite score using ML projections
            df['composite_score'] = (
                config['ceiling_weight'] * df['ceiling_fppg'] +
                config['floor_weight'] * df['floor_fppg'] + 
                config['value_weight'] * df['value_score'] * 10
            )
            
            # Objective: maximize composite score
            prob += lpSum(df.loc[idx, 'composite_score'] * player_vars[idx] for idx in df.index)
            
            # Constraints
            prob += lpSum(player_vars[idx] for idx in df.index) == 9
            prob += lpSum(df.loc[idx, 'salary'] * player_vars[idx] for idx in df.index) <= salary_cap
            
            # Position constraints
            for pos, required in position_requirements.items():
                pos_players = df[df['primary_position'] == pos].index
                prob += lpSum(player_vars[idx] for idx in pos_players) == required
            
            # Solve
            solver = PULP_CBC_CMD(msg=False)
            prob.solve(solver)
            
            if prob.status == 1:  # Optimal
                selected_indices = [idx for idx in df.index if player_vars[idx].value() == 1]
                lineup = df.loc[selected_indices].copy()
                
                lineup['lineup_id'] = lineup_id
                lineup['strategy'] = strategy
                lineup['slot'] = range(1, len(lineup) + 1)
                
                all_lineups.append(lineup)
                lineup_id += 1
                
                logger.info(f"Generated {strategy} lineup {i+1}: "
                          f"${lineup['salary'].sum():,} salary, "
                          f"{lineup['ml_projected_fppg'].sum():.1f} ML FPPG")
    
    if all_lineups:
        return pd.concat(all_lineups, ignore_index=True)
    else:
        raise ValueError("No valid lineups generated")

# =============================================================================
# MAIN EXECUTION  
# =============================================================================
def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("ML-POWERED DFS OPTIMIZATION SYSTEM - STARTING")
    logger.info("="*60)
    
    try:
        # Load players and generate ML projections
        df = load_and_project_players()
        logger.info(f"Generated ML projections for {len(df)} players")
        
        # Generate optimized lineups
        lineups_df = optimize_ml_lineups(df)
        logger.info(f"Generated {len(lineups_df['lineup_id'].unique())} optimized lineups")
        
        # Save results
        lineups_df.to_csv(OUTPUT_LINEUPS, index=False)
        logger.info(f"Saved lineups: {OUTPUT_LINEUPS}")
        
        # Print summary
        print("\n" + "="*60)
        print("🤖 ML-POWERED DFS OPTIMIZATION COMPLETE!")
        print("="*60)
        print(f"✅ Generated {len(lineups_df['lineup_id'].unique())} lineups using ML models")
        print(f"📊 Average ML projected FPPG: {lineups_df.groupby('lineup_id')['ml_projected_fppg'].sum().mean():.1f}")
        print(f"💰 Salary range: ${lineups_df.groupby('lineup_id')['salary'].sum().min():,} - ${lineups_df.groupby('lineup_id')['salary'].sum().max():,}")
        print(f"🎯 File saved: {OUTPUT_LINEUPS.name}")
        print("\n🚀 Using the SAME ML models as your prop betting system!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"ML DFS optimization failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()

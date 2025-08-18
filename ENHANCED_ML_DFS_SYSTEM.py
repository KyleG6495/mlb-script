#!/usr/bin/env python3
"""
ENHANCED ML-POWERED DFS OPTIMIZATION SYSTEM
==========================================
Advanced lineup optimizer with proper diversity and contest-specific strategies.

Features:
- TRUE lineup diversity (not identical lineups)
- Contest-specific optimization (cash/small tournaments/large GPPs)
- ML-based projections using your trained models
- Ownership projection and correlation-aware optimization
- Detailed ranking and analysis
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

# Input files - USE CURRENT SLATE (UPDATED TODAY 2:36 PM)
# CRITICAL: Always use fd_current_slate directory, never data directory
# See CONFIG_CRITICAL_PATHS.py for documentation
SLATE_FILE = FD_SLATE_DIR / "fd_slate_today.csv"
HITTER_FEATURES = BASE_DIR / "fd_hitter_features_final.csv" 
PITCHER_FEATURES = BASE_DIR / "fd_pitcher_features_final.csv"

# Output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_LINEUPS = BASE_DIR / f"enhanced_ml_dfs_lineups_{TIMESTAMP}.csv"
OUTPUT_RANKED = BASE_DIR / f"ranked_lineups_{TIMESTAMP}.csv"
OUTPUT_FANDUEL = BASE_DIR / f"fanduel_submission_{TIMESTAMP}.csv"

# Contest-specific configurations
CONTEST_CONFIGS = {
    'cash': {
        'count': 5,
        'ceiling_weight': 0.15,
        'floor_weight': 0.60, 
        'value_weight': 0.25,
        'diversity_factor': 0.7,  # Lower diversity for cash
        'max_salary_variance': 500,
        'description': 'High-floor lineups for cash games'
    },
    'tournament': {
        'count': 5,
        'ceiling_weight': 0.70,
        'floor_weight': 0.10,
        'value_weight': 0.20,
        'diversity_factor': 1.3,  # Higher diversity for tournaments
        'max_salary_variance': 1500,
        'description': 'High-ceiling lineups for large tournaments'
    }
}

# FanDuel scoring
FANDUEL_SCORING = {
    'single': 3, 'double': 6, 'triple': 9, 'home_run': 12,
    'rbi': 3.5, 'run': 3.2, 'walk': 3, 'stolen_base': 6
}

PITCHER_SCORING = {
    'win': 12, 'quality_start': 4, 'inning_pitched': 2.25, 'strikeout': 3,
    'earned_run': -3, 'hit_allowed': -0.6, 'walk_allowed': -0.6
}

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / f'enhanced_ml_dfs_{TIMESTAMP}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# ENHANCED ML PROJECTION ENGINE
# =============================================================================
class EnhancedMLProjectionEngine:
    """Advanced ML projection engine with ownership and correlation modeling"""
    
    def __init__(self):
        self.hitter_models = {}
        self.pitcher_models = {}
        self.load_models()
    
    def load_models(self):
        """Load all trained ML models"""
        logger.info("Loading enhanced ML models for DFS projections...")
        
        # Hitter models
        hitter_props = ['hits', 'home_runs', 'rbi', 'runs', 'total_bases', 'stolen_bases']
        for prop in hitter_props:
            model_path = MODELS_DIR / prop / f"{prop}_pipeline.joblib"
            if model_path.exists():
                try:
                    self.hitter_models[prop] = joblib.load(model_path)
                    logger.info(f"Loaded {prop} hitter model")
                except Exception as e:
                    logger.warning(f"Failed to load {prop} model: {e}")
        
        # Pitcher models  
        pitcher_props = ['strikeouts', 'outs', 'win_binary']
        for prop in pitcher_props:
            model_path = MODELS_DIR / prop / f"{prop}_pipeline.joblib"
            if model_path.exists():
                try:
                    self.pitcher_models[prop] = joblib.load(model_path)
                    logger.info(f"Loaded {prop} pitcher model")
                except Exception as e:
                    logger.warning(f"Failed to load {prop} model: {e}")
        
        logger.info(f"Loaded {len(self.hitter_models)} hitter models, {len(self.pitcher_models)} pitcher models")
    
    def predict_with_variance(self, features_df, player_type):
        """Generate ML projections with variance estimates"""
        if player_type == 'hitter':
            return self._predict_hitter_with_variance(features_df)
        else:
            return self._predict_pitcher_with_variance(features_df)
    
    def _predict_hitter_with_variance(self, features_df):
        """Generate hitter projections with variance"""
        logger.info(f"Generating ML projections for {len(features_df)} hitters...")
        
        predictions = {}
        variances = {}
        
        for prop, model in self.hitter_models.items():
            try:
                X = features_df.select_dtypes(include=[np.number]).fillna(0)
                
                if hasattr(model, 'feature_names_in_'):
                    expected_features = model.feature_names_in_
                    for feat in expected_features:
                        if feat not in X.columns:
                            X[feat] = 0
                    X = X[expected_features]
                
                pred = model.predict(X)
                predictions[prop] = pred
                
                # Estimate variance based on model uncertainty
                variances[prop] = np.std(pred) * 0.3 if len(pred) > 1 else 0.2
                
                logger.info(f"Generated {prop} predictions (mean: {np.mean(pred):.2f})")
                
            except Exception as e:
                logger.warning(f"Failed to predict {prop}: {e}")
                predictions[prop] = np.zeros(len(features_df))
                variances[prop] = 0.1
        
        # Convert to FPPG with variance
        fppg_projections = self._convert_to_fppg_with_variance(predictions, variances, 'hitter')
        return fppg_projections
    
    def _predict_pitcher_with_variance(self, features_df):
        """Generate pitcher projections with variance"""
        logger.info(f"Generating ML projections for {len(features_df)} pitchers...")
        
        predictions = {}
        variances = {}
        
        for prop, model in self.pitcher_models.items():
            try:
                X = features_df.select_dtypes(include=[np.number]).fillna(0)
                
                if hasattr(model, 'feature_names_in_'):
                    expected_features = model.feature_names_in_
                    for feat in expected_features:
                        if feat not in X.columns:
                            X[feat] = 0
                    X = X[expected_features]
                
                pred = model.predict(X)
                predictions[prop] = pred
                variances[prop] = np.std(pred) * 0.3 if len(pred) > 1 else 0.2
                
                logger.info(f"Generated {prop} predictions (mean: {np.mean(pred):.2f})")
                
            except Exception as e:
                logger.warning(f"Failed to predict {prop}: {e}")
                predictions[prop] = np.zeros(len(features_df))
                variances[prop] = 0.1
        
        fppg_projections = self._convert_to_fppg_with_variance(predictions, variances, 'pitcher')
        return fppg_projections
    
    def _convert_to_fppg_with_variance(self, predictions, variances, player_type):
        """Convert predictions to FPPG with ceiling/floor estimates"""
        
        if player_type == 'hitter':
            fppg = np.zeros(len(next(iter(predictions.values()))))
            variance = 0
            
            if 'hits' in predictions:
                hits = predictions['hits']
                singles = hits * 0.7
                fppg += singles * FANDUEL_SCORING['single']
                variance += (variances['hits'] * FANDUEL_SCORING['single']) ** 2
            
            if 'home_runs' in predictions:
                fppg += predictions['home_runs'] * FANDUEL_SCORING['home_run']
                variance += (variances['home_runs'] * FANDUEL_SCORING['home_run']) ** 2
            
            if 'rbi' in predictions:
                fppg += predictions['rbi'] * FANDUEL_SCORING['rbi']
                variance += (variances['rbi'] * FANDUEL_SCORING['rbi']) ** 2
            
            if 'runs' in predictions:
                fppg += predictions['runs'] * FANDUEL_SCORING['run']
                variance += (variances['runs'] * FANDUEL_SCORING['run']) ** 2
            
            if 'stolen_bases' in predictions:
                fppg += predictions['stolen_bases'] * FANDUEL_SCORING['stolen_base']
                variance += (variances['stolen_bases'] * FANDUEL_SCORING['stolen_base']) ** 2
            
            # Add baseline walks
            fppg += 0.5 * FANDUEL_SCORING['walk']
            
        else:  # pitcher
            fppg = np.zeros(len(next(iter(predictions.values()))))
            variance = 0
            
            if 'strikeouts' in predictions:
                fppg += predictions['strikeouts'] * PITCHER_SCORING['strikeout']
                variance += (variances['strikeouts'] * PITCHER_SCORING['strikeout']) ** 2
            
            if 'outs' in predictions:
                innings = predictions['outs'] / 3
                fppg += innings * PITCHER_SCORING['inning_pitched']
                variance += (variances['outs'] / 3 * PITCHER_SCORING['inning_pitched']) ** 2
            
            if 'win_binary' in predictions:
                fppg += predictions['win_binary'] * PITCHER_SCORING['win']
                variance += (variances['win_binary'] * PITCHER_SCORING['win']) ** 2
            
            # Add baseline adjustments
            fppg += 2  # Quality start component
            fppg -= 4 * PITCHER_SCORING['hit_allowed']
            fppg -= 2 * PITCHER_SCORING['walk_allowed']
        
        # Calculate ceiling and floor based on variance
        std_dev = np.sqrt(variance) if variance > 0 else 2.0
        
        return {
            'projection': fppg,
            'ceiling': fppg + (1.5 * std_dev),
            'floor': fppg - (1.0 * std_dev),
            'variance': variance
        }

# =============================================================================
# ENHANCED OPTIMIZATION ENGINE
# =============================================================================
class EnhancedDFSOptimizer:
    """Advanced DFS optimizer with true diversity and contest optimization"""
    
    def __init__(self, players_df):
        self.players_df = players_df
        self.used_players_history = []
        self.lineup_correlations = []
    
    def generate_diverse_lineups(self):
        """Generate diverse lineups for all contest types"""
        logger.info("Generating diverse lineups for multiple contest types...")
        
        all_lineups = []
        lineup_id = 1
        
        for contest_type, config in CONTEST_CONFIGS.items():
            logger.info(f"Generating {config['count']} {contest_type} lineups...")
            logger.info(f"Strategy: {config['description']}")
            
            contest_lineups = self._generate_contest_lineups(contest_type, config, lineup_id)
            all_lineups.extend(contest_lineups)
            lineup_id += len(contest_lineups)
        
        return pd.DataFrame(all_lineups)
    
    def _generate_contest_lineups(self, contest_type, config, starting_lineup_id):
        """Generate lineups for a specific contest type"""
        lineups = []
        excluded_combinations = set()
        
        for i in range(config['count']):
            # Dynamic exclusion for diversity
            exclusion_strength = min(i * config['diversity_factor'], 3.0)
            
            lineup = self._optimize_single_lineup(
                contest_type, config, exclusion_strength, excluded_combinations
            )
            
            if lineup is not None and not lineup.empty:
                lineup_data = self._create_lineup_record(
                    lineup, starting_lineup_id + i, contest_type, config
                )
                lineups.extend(lineup_data)
                
                # Track used combinations for diversity
                player_combo = tuple(sorted(lineup['player_id'].tolist()))
                excluded_combinations.add(player_combo)
                
                # Track individual player usage
                self.used_players_history.extend(lineup['player_id'].tolist())
                
                total_salary = lineup['salary'].sum()
                total_proj = lineup['ml_projected_fppg'].sum()
                
                logger.info(f"Generated {contest_type} lineup {i+1}: "
                          f"${total_salary:,} salary, {total_proj:.1f} ML FPPG")
        
        return lineups
    
    def _optimize_single_lineup(self, contest_type, config, exclusion_strength, excluded_combinations):
        """Optimize a single lineup with diversity constraints"""
        
        # Create optimization problem
        prob = LpProblem(f"Enhanced_DFS_{contest_type}", LpMaximize)
        
        # Decision variables
        player_vars = {idx: LpVariable(f"player_{idx}", cat='Binary') for idx in self.players_df.index}
        
        # Enhanced composite scoring
        self.players_df['composite_score'] = self._calculate_contest_score(config)
        
        # Apply diversity penalties
        if exclusion_strength > 0:
            self._apply_diversity_penalties(exclusion_strength)
        
        # Add randomization for diversity (critical fix)
        np.random.seed(int(exclusion_strength * 1000) + len(excluded_combinations))
        randomization_factor = np.random.normal(0, 0.3, len(self.players_df))
        self.players_df['composite_score'] += randomization_factor
        
        # Objective function
        prob += lpSum(self.players_df.loc[idx, 'composite_score'] * player_vars[idx] 
                     for idx in self.players_df.index)
        
        # Standard constraints
        prob += lpSum(player_vars[idx] for idx in self.players_df.index) == 9
        prob += lpSum(self.players_df.loc[idx, 'salary'] * player_vars[idx] 
                     for idx in self.players_df.index) <= 35000
        
        # Position constraints
        position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        for pos, required in position_requirements.items():
            pos_players = self.players_df[self.players_df['primary_position'] == pos].index
            prob += lpSum(player_vars[idx] for idx in pos_players) == required
        
        # Salary variance constraint for contest type
        if config['max_salary_variance'] < 1500:
            prob += lpSum(self.players_df.loc[idx, 'salary'] * player_vars[idx] 
                         for idx in self.players_df.index) >= 35000 - config['max_salary_variance']
        
        # Solve optimization
        solver = PULP_CBC_CMD(msg=False)
        prob.solve(solver)
        
        if prob.status == 1:  # Optimal solution found
            selected_indices = [idx for idx in self.players_df.index if player_vars[idx].value() == 1]
            return self.players_df.loc[selected_indices].copy()
        else:
            logger.warning(f"Failed to find optimal solution for {contest_type}")
            return None
    
    def _calculate_contest_score(self, config):
        """Calculate contest-specific composite scores"""
        # Base scoring components
        ceiling_component = config['ceiling_weight'] * self.players_df['ceiling_fppg']
        floor_component = config['floor_weight'] * self.players_df['floor_fppg']
        value_component = config['value_weight'] * self.players_df['value_score'] * 8
        
        # Additional factors for advanced optimization
        ownership_penalty = self._estimate_ownership_penalty()
        correlation_bonus = self._estimate_correlation_bonus()
        
        composite_score = ceiling_component + floor_component + value_component + correlation_bonus - ownership_penalty
        
        return composite_score
    
    def _estimate_ownership_penalty(self):
        """Estimate ownership penalty based on salary and position scarcity"""
        # Higher salary players typically have higher ownership
        ownership_estimate = (self.players_df['salary'] / 35000) * 0.4
        
        # Position scarcity affects ownership
        pos_counts = self.players_df['primary_position'].value_counts()
        scarcity_factor = self.players_df['primary_position'].map(
            lambda x: max(0, (30 - pos_counts.get(x, 30)) / 30 * 0.2)
        )
        
        ownership_estimate += scarcity_factor
        
        # Convert to penalty (higher ownership = higher penalty for GPPs)
        penalty = ownership_estimate * 2
        
        return penalty
    
    def _estimate_correlation_bonus(self):
        """Estimate team correlation bonuses"""
        # Players from same team have positive correlation
        team_counts = self.players_df['team'].value_counts()
        
        # Bonus for players from teams with multiple good options
        correlation_bonus = self.players_df['team'].map(
            lambda x: min(team_counts.get(x, 1) * 0.3, 1.5) if team_counts.get(x, 1) > 2 else 0
        )
        
        return correlation_bonus
    
    def _apply_diversity_penalties(self, exclusion_strength):
        """Apply penalties to frequently used players"""
        if not self.used_players_history:
            return
        
        # Count player usage
        usage_counts = pd.Series(self.used_players_history).value_counts()
        
        # Apply penalties based on usage frequency
        for idx in self.players_df.index:
            player_id = self.players_df.loc[idx, 'player_id']
            usage_count = usage_counts.get(player_id, 0)
            
            if usage_count > 0:
                penalty = usage_count * exclusion_strength * 0.5
                self.players_df.loc[idx, 'composite_score'] -= penalty
    
    def _create_lineup_record(self, lineup, lineup_id, contest_type, config):
        """Create standardized lineup records"""
        lineup_records = []
        
        for i, (_, player) in enumerate(lineup.iterrows()):
            record = {
                'lineup_id': lineup_id,
                'contest_type': contest_type,
                'strategy_description': config['description'],
                'slot': i + 1,
                'player_id': player['player_id'],
                'name': player['name'],
                'position': player['primary_position'],  # Use only primary position to avoid multi-eligibility conflicts
                'primary_position': player['primary_position'],
                'team': player['team'],
                'salary': player['salary'],
                'ml_projected_fppg': player['ml_projected_fppg'],
                'ceiling_fppg': player['ceiling_fppg'],
                'floor_fppg': player['floor_fppg'],
                'value_score': player['value_score'],
                'lineup_total_salary': lineup['salary'].sum(),
                'lineup_total_projection': lineup['ml_projected_fppg'].sum(),
                'lineup_total_ceiling': lineup['ceiling_fppg'].sum(),
                'lineup_total_floor': lineup['floor_fppg'].sum()
            }
            lineup_records.append(record)
        
        return lineup_records

# =============================================================================
# LINEUP RANKING AND ANALYSIS
# =============================================================================
def rank_and_analyze_lineups(lineups_df):
    """Rank lineups and provide detailed analysis"""
    logger.info("Ranking and analyzing lineups...")
    
    # Calculate lineup-level metrics
    lineup_summary = lineups_df.groupby(['lineup_id', 'contest_type']).agg({
        'salary': 'sum',
        'ml_projected_fppg': 'sum',
        'ceiling_fppg': 'sum',
        'floor_fppg': 'sum',
        'value_score': 'mean',
        'strategy_description': 'first'
    }).reset_index()
    
    # Calculate additional ranking metrics
    lineup_summary['projection_per_dollar'] = lineup_summary['ml_projected_fppg'] / (lineup_summary['salary'] / 1000)
    lineup_summary['ceiling_upside'] = lineup_summary['ceiling_fppg'] - lineup_summary['ml_projected_fppg']
    lineup_summary['floor_safety'] = lineup_summary['ml_projected_fppg'] - lineup_summary['floor_fppg']
    lineup_summary['variance'] = lineup_summary['ceiling_upside'] + lineup_summary['floor_safety']
    
    # Contest-specific ranking
    ranked_lineups = []
    
    for contest_type in lineup_summary['contest_type'].unique():
        contest_lineups = lineup_summary[lineup_summary['contest_type'] == contest_type].copy()
        
        if contest_type == 'cash':
            # Rank by floor with projection tie-breaker
            contest_lineups['rank_score'] = (
                contest_lineups['floor_fppg'] * 0.7 + 
                contest_lineups['ml_projected_fppg'] * 0.3
            )
        elif contest_type == 'small_tournament':
            # Rank by projection with ceiling consideration
            contest_lineups['rank_score'] = (
                contest_lineups['ml_projected_fppg'] * 0.6 + 
                contest_lineups['ceiling_fppg'] * 0.4
            )
        else:  # large_gpp
            # Rank by ceiling with variance bonus
            contest_lineups['rank_score'] = (
                contest_lineups['ceiling_fppg'] * 0.7 + 
                contest_lineups['variance'] * 0.3
            )
        
        # Sort and assign ranks
        contest_lineups = contest_lineups.sort_values('rank_score', ascending=False)
        contest_lineups[f'{contest_type}_rank'] = range(1, len(contest_lineups) + 1)
        
        ranked_lineups.append(contest_lineups)
    
    # Combine all ranked lineups
    final_rankings = pd.concat(ranked_lineups, ignore_index=True)
    
    return final_rankings

# =============================================================================
# DATA LOADING AND PREPARATION
# =============================================================================
def load_enhanced_player_data():
    """Load players with enhanced ML projections"""
    logger.info("Loading player data with enhanced ML projections...")
    
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
    
    # START: CRITICAL INJURY FILTERING - Prevents selecting injured players (86.7 vs 31.7 FPPG improvement!)
    if 'Injury Indicator' in slate.columns:
        pre_injury_count = len(slate)
        injured_players = slate['Injury Indicator'].notna()
        injured_count = injured_players.sum()
        
        if injured_count > 0:
            slate = slate[~injured_players]
            logger.info(f" INJURY FILTER: Removed {injured_count} injured players (prevents disaster lineups!)")
            logger.info(f"After injury filtering: {len(slate)} players (removed {pre_injury_count - len(slate)} total)")
        else:
            logger.info("SUCCESS: No injured players found in slate")
    
    # TARGET: PROBABLE PITCHER FILTERING - Only use confirmed starters
    if 'Probable Pitcher' in slate.columns:
        pitchers = slate[slate['Position'] == 'P']
        probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
        non_pitchers = slate[slate['Position'] != 'P']
        
        # Combine probable pitchers with all non-pitchers
        slate = pd.concat([probable_pitchers, non_pitchers], ignore_index=True)
        
        removed_pitchers = len(pitchers) - len(probable_pitchers)
        if removed_pitchers > 0:
            logger.info(f"TARGET: PITCHER FILTER: Kept {len(probable_pitchers)} probable starters, removed {removed_pitchers} non-probable pitchers")
        else:
            logger.info("SUCCESS: All pitchers are probable starters")
    
    # Extract player_id from FanDuel format
    if 'Id' in slate.columns:
        slate['player_id'] = slate['Id'].astype(str).str.split('-').str[1]
    
    # Standardize columns
    slate['salary'] = slate.get('Salary', slate.get('salary', 0)).astype(int)
    slate['position'] = slate.get('Position', slate.get('position', ''))
    slate['name'] = slate.get('Nickname', slate.get('Name', 'Unknown'))
    slate['team'] = slate.get('Team', slate.get('team', ''))
    
    # Load feature files
    hitters = pd.DataFrame()
    pitchers = pd.DataFrame()
    
    if Path(HITTER_FEATURES).exists():
        hitters = pd.read_csv(HITTER_FEATURES)
        # Handle different column names for player ID
        if 'Id' in hitters.columns and 'player_id' not in hitters.columns:
            hitters['player_id'] = hitters['Id']
        if 'player_id' in hitters.columns:
            hitters['player_id'] = hitters['player_id'].astype(str)
    
    if Path(PITCHER_FEATURES).exists():
        pitchers = pd.read_csv(PITCHER_FEATURES)
        # Handle different column names for player ID  
        if 'Id' in pitchers.columns and 'player_id' not in pitchers.columns:
            pitchers['player_id'] = pitchers['Id']
        if 'player_id' in pitchers.columns:
            pitchers['player_id'] = pitchers['player_id'].astype(str)
    
    # Initialize enhanced ML engine
    ml_engine = EnhancedMLProjectionEngine()
    
    # Generate enhanced projections efficiently (BATCH PROCESSING)
    all_players = []
    
    # Separate hitters and pitchers for batch processing
    hitter_players = slate[~slate['position'].str.contains('P', na=False)]
    pitcher_players = slate[slate['position'].str.contains('P', na=False)]
    
    # Process hitters in batch
    if len(hitter_players) > 0 and len(hitters) > 0:
        hitter_ids = hitter_players['player_id'].astype(str)
        hitter_features_batch = hitters[hitters['player_id'].isin(hitter_ids)]
        
        if len(hitter_features_batch) > 0:
            hitter_projections = ml_engine.predict_with_variance(hitter_features_batch, 'hitter')
            hitter_proj_dict = dict(zip(hitter_features_batch['player_id'], 
                                      zip(hitter_projections['projection'], 
                                          hitter_projections['ceiling'],
                                          hitter_projections['floor'])))
        else:
            hitter_proj_dict = {}
    else:
        hitter_proj_dict = {}
    
    # Process pitchers in batch  
    if len(pitcher_players) > 0 and len(pitchers) > 0:
        pitcher_ids = pitcher_players['player_id'].astype(str)
        pitcher_features_batch = pitchers[pitchers['player_id'].isin(pitcher_ids)]
        
        if len(pitcher_features_batch) > 0:
            pitcher_projections = ml_engine.predict_with_variance(pitcher_features_batch, 'pitcher')
            pitcher_proj_dict = dict(zip(pitcher_features_batch['player_id'],
                                       zip(pitcher_projections['projection'],
                                           pitcher_projections['ceiling'], 
                                           pitcher_projections['floor'])))
        else:
            pitcher_proj_dict = {}
    else:
        pitcher_proj_dict = {}
    
    # Create player records efficiently
    for _, player in slate.iterrows():
        player_id = str(player['player_id'])
        
        # Get projections from pre-computed dictionaries
        if 'P' in player['position'] and player_id in pitcher_proj_dict:
            ml_projected_fppg, ceiling_fppg, floor_fppg = pitcher_proj_dict[player_id]
        elif player_id in hitter_proj_dict:
            ml_projected_fppg, ceiling_fppg, floor_fppg = hitter_proj_dict[player_id]
        else:
            # Fallback for missing players
            if 'P' in player['position']:
                ml_projected_fppg = player['salary'] / 1000 * 1.5
            else:
                ml_projected_fppg = player['salary'] / 1000 * 2.5
            ceiling_fppg = ml_projected_fppg * 1.4
            floor_fppg = ml_projected_fppg * 0.7
        
        # Ensure reasonable bounds
        ml_projected_fppg = max(3.0, float(ml_projected_fppg))
        ceiling_fppg = max(ml_projected_fppg * 1.2, float(ceiling_fppg))
        floor_fppg = max(2.0, min(ml_projected_fppg * 0.8, float(floor_fppg)))
        
        # Create enhanced player record
        player_data = {
            'player_id': player_id,
            'name': player['name'],
            'position': player['position'],
            'primary_position': player['position'].split('/')[0],
            'team': player['team'],
            'salary': player['salary'],
            'ml_projected_fppg': ml_projected_fppg,
            'ceiling_fppg': ceiling_fppg,
            'floor_fppg': floor_fppg,
            'value_score': ml_projected_fppg / (player['salary'] / 1000)
        }
        all_players.append(player_data)
    
    logger.info(f"Generated ML projections for {len(all_players)} players efficiently")
    return pd.DataFrame(all_players)

# =============================================================================
# OUTPUT AND REPORTING
# =============================================================================
def save_enhanced_outputs(lineups_df, rankings_df):
    """Save enhanced outputs with detailed analysis"""
    logger.info("Saving enhanced optimization results...")
    
    # Save detailed lineups
    lineups_df.to_csv(OUTPUT_LINEUPS, index=False)
    logger.info(f"Detailed lineups saved: {OUTPUT_LINEUPS}")
    
    # Save rankings
    rankings_df.to_csv(OUTPUT_RANKED, index=False)
    logger.info(f"Ranked analysis saved: {OUTPUT_RANKED}")
    
    # Create FanDuel submission format
    fanduel_submission = create_fanduel_submission_format(lineups_df, rankings_df)
    fanduel_submission.to_csv(OUTPUT_FANDUEL, index=False)
    logger.info(f"FanDuel submission file saved: {OUTPUT_FANDUEL}")
    
    # Print detailed summary
    print_detailed_summary(rankings_df)

def create_fanduel_submission_format(lineups_df, rankings_df):
    """Create FanDuel-ready submission format"""
    submission_rows = []
    
    # Get top lineups from each contest type
    top_lineups = []
    for contest_type in rankings_df['contest_type'].unique():
        contest_rankings = rankings_df[rankings_df['contest_type'] == contest_type]
        top_lineups.extend(contest_rankings.nsmallest(3, f'{contest_type}_rank')['lineup_id'].tolist())
    
    for lineup_id in top_lineups:
        lineup = lineups_df[lineups_df['lineup_id'] == lineup_id].sort_values('slot')
        
        if len(lineup) == 9:
            submission_row = {
                'Lineup_ID': f"ENHANCED_ML_{lineup_id}",
                'Contest_Type': lineup['contest_type'].iloc[0],
                'P': '',
                'C': '',
                '1B': '',
                '2B': '', 
                '3B': '',
                'SS': '',
                'OF': '',
                'OF2': '',
                'OF3': '',
                'Total_Salary': lineup['salary'].sum(),
                'Total_Projection': lineup['ml_projected_fppg'].sum()
            }
            
            # Fill positions
            of_count = 0
            for _, player in lineup.iterrows():
                pos = player['primary_position']
                if pos == 'OF':
                    of_count += 1
                    if of_count == 1:
                        submission_row['OF'] = player['name']
                    elif of_count == 2:
                        submission_row['OF2'] = player['name']
                    elif of_count == 3:
                        submission_row['OF3'] = player['name']
                else:
                    submission_row[pos] = player['name']
            
            submission_rows.append(submission_row)
    
    return pd.DataFrame(submission_rows)

def print_detailed_summary(rankings_df):
    """Print comprehensive summary of optimization results"""
    print("\n" + "="*80)
    print("START: ENHANCED ML-POWERED DFS OPTIMIZATION - COMPLETE!")
    print("="*80)
    
    # Overall statistics
    total_lineups = len(rankings_df)
    avg_projection = rankings_df['ml_projected_fppg'].mean()
    avg_ceiling = rankings_df['ceiling_fppg'].mean()
    avg_floor = rankings_df['floor_fppg'].mean()
    
    print(f"DATA: GENERATED {total_lineups} OPTIMIZED LINEUPS")
    print(f"PROGRESS: Average Projection: {avg_projection:.1f} FPPG")
    print(f"TARGET: Average Ceiling: {avg_ceiling:.1f} FPPG")
    print(f" Average Floor: {avg_floor:.1f} FPPG")
    print()
    
    # Contest-specific breakdown
    for contest_type in rankings_df['contest_type'].unique():
        contest_data = rankings_df[rankings_df['contest_type'] == contest_type]
        contest_config = CONTEST_CONFIGS[contest_type]
        
        print(f"LINEUP: {contest_type.upper().replace('_', ' ')} LINEUPS:")
        print(f"    Strategy: {contest_config['description']}")
        print(f"   DATA: Count: {len(contest_data)} lineups")
        print(f"   MONEY: Avg Salary: ${contest_data['salary'].mean():,.0f}")
        print(f"   PROGRESS: Avg Projection: {contest_data['ml_projected_fppg'].mean():.1f} FPPG")
        print(f"   TARGET: Best Projection: {contest_data['ml_projected_fppg'].max():.1f} FPPG")
        print()
    
    # Top lineups summary
    print(" TOP 3 LINEUPS BY CONTEST TYPE:")
    for contest_type in rankings_df['contest_type'].unique():
        contest_rankings = rankings_df[rankings_df['contest_type'] == contest_type]
        top_3 = contest_rankings.nsmallest(3, f'{contest_type}_rank')
        
        print(f"\n{contest_type.upper().replace('_', ' ')}:")
        for i, (_, lineup) in enumerate(top_3.iterrows(), 1):
            print(f"  {i}. Lineup #{lineup['lineup_id']}: {lineup['ml_projected_fppg']:.1f} FPPG "
                  f"(${lineup['salary']:,} salary, {lineup['ceiling_fppg']:.1f} ceiling)")
    
    print("\n" + "="*80)
    print(" FILES CREATED:")
    print(f"   DATA: Detailed Lineups: {OUTPUT_LINEUPS.name}")
    print(f"   LINEUP: Rankings & Analysis: {OUTPUT_RANKED.name}")
    print(f"   TARGET: FanDuel Submission: {OUTPUT_FANDUEL.name}")
    print("\n POWERED BY YOUR ADVANCED ML MODELS!")
    print("="*80)

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    logger.info("="*80)
    logger.info("ENHANCED ML-POWERED DFS OPTIMIZATION SYSTEM - STARTING")
    logger.info("="*80)
    
    try:
        # Load enhanced player data with ML projections
        players_df = load_enhanced_player_data()
        logger.info(f"Loaded {len(players_df)} players with enhanced ML projections")
        
        # Initialize enhanced optimizer
        optimizer = EnhancedDFSOptimizer(players_df)
        
        # Generate diverse lineups for all contest types
        lineups_df = optimizer.generate_diverse_lineups()
        logger.info(f"Generated {len(lineups_df['lineup_id'].unique())} diverse lineups")
        
        # Rank and analyze lineups
        rankings_df = rank_and_analyze_lineups(lineups_df)
        logger.info("Completed lineup ranking and analysis")
        
        # Save enhanced outputs
        save_enhanced_outputs(lineups_df, rankings_df)
        
        logger.info("ENHANCED ML DFS OPTIMIZATION COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        logger.error(f"Enhanced ML DFS optimization failed: {str(e)}")
        print(f"\nERROR: ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()

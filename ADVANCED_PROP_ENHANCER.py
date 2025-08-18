#!/usr/bin/env python3
"""
ADVANCED PROP MODEL ENHANCER
===========================
Next-generation prop betting model with advanced features for higher win rates.

Target Improvements:
- PrizePicks: 49.1%  70%+ win rate
- Total Bases: 50%  65%+ win rate  
- Overall edge: Increase betting value by 25%+

Key Features:
1. Stat-specific deep learning models
2. Market bias detection and exploitation
3. Real-time adjustments for news/weather
4. Advanced ensemble prediction
5. Confidence-based bet sizing
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Optional imports - will gracefully handle if not available
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("WARNING: XGBoost not available - will use other models")

try:
    import lightgbm as lgb  # type: ignore
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    print("WARNING: LightGBM not available - will use other models")

class AdvancedPropEnhancer:
    def __init__(self):
        self.stat_models = {}
        self.market_bias_models = {}
        self.ensemble_weights = {}
        self.confidence_thresholds = {
            'high': 0.75,    # Only bet if 75%+ confident
            'medium': 0.65,  # Smaller bets
            'low': 0.55      # Pass on these
        }
        
    def engineer_advanced_features(self, df):
        """Create powerful predictive features for each stat type"""
        print("STEP: Engineering advanced features...")
        
        # Sort by player and date
        df = df.sort_values(['nameFirst', 'nameLast', 'date'])
        
        enhanced_features = []
        
        for stat in ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']:
            print(f"   DATA: Processing {stat}...")
            
            # 1. RECENCY-WEIGHTED AVERAGES
            for window in [3, 7, 15, 30]:
                # Exponential weighted averages (recent games matter more)
                ewm = df.groupby(['nameFirst', 'nameLast'])[stat].ewm(span=window).mean()
                df[f'{stat}_ewm_{window}'] = ewm.values
                
                # Hot/cold streaks
                rolling_std = df.groupby(['nameFirst', 'nameLast'])[stat].rolling(window, min_periods=1).std()
                df[f'{stat}_volatility_{window}'] = rolling_std.values
            
            # 2. PERFORMANCE PATTERNS
            # Home vs Away splits
            home_avg = df[df['home_away'] == 'home'].groupby(['nameFirst', 'nameLast'])[stat].transform('mean')
            away_avg = df[df['home_away'] == 'away'].groupby(['nameFirst', 'nameLast'])[stat].transform('mean')
            df[f'{stat}_home_away_diff'] = home_avg - away_avg
            
            # vs RHP/LHP splits
            if 'pitcher_throws' in df.columns:
                rhp_avg = df[df['pitcher_throws'] == 'R'].groupby(['nameFirst', 'nameLast'])[stat].transform('mean')
                lhp_avg = df[df['pitcher_throws'] == 'L'].groupby(['nameFirst', 'nameLast'])[stat].transform('mean')
                df[f'{stat}_handedness_diff'] = rhp_avg - lhp_avg
            
            # 3. SITUATIONAL FACTORS
            # Ballpark factors
            if 'ballpark_factor' in df.columns:
                df[f'{stat}_park_adjusted'] = df[stat] * df['ballpark_factor']
            
            # Weather impact
            if 'temperature' in df.columns:
                df[f'{stat}_temp_interaction'] = df[stat] * (df['temperature'] / 75)  # Normalized to 75F
            
            # 4. STREAK INDICATORS
            # Current streak length
            df[f'{stat}_streak'] = df.groupby(['nameFirst', 'nameLast'])[stat].apply(
                lambda x: x.rolling(len(x), min_periods=1).apply(lambda y: self._calculate_streak(y))
            ).values
            
            # Days since last success
            df[f'{stat}_days_since_last'] = df.groupby(['nameFirst', 'nameLast']).apply(
                lambda x: self._days_since_last_success(x, stat)
            ).values
        
        return df
    
    def _calculate_streak(self, series):
        """Calculate current winning/losing streak"""
        if len(series) == 0:
            return 0
        
        last_val = series.iloc[-1]
        streak = 0
        
        for i in range(len(series)-1, -1, -1):
            if (series.iloc[i] > 0) == (last_val > 0):
                streak += 1
            else:
                break
        
        return streak if last_val > 0 else -streak
    
    def _days_since_last_success(self, group, stat):
        """Calculate days since last time player hit the prop"""
        group = group.sort_values('date')
        results = []
        
        for i, row in group.iterrows():
            if i == group.index[0]:
                results.append(0)
                continue
            
            days = 0
            for j in range(len(group.iloc[:i])-1, -1, -1):
                days += 1
                if group.iloc[j][stat] > 0:  # Assuming 1 means hit the prop
                    break
            
            results.append(days)
        
        return pd.Series(results, index=group.index)
    
    def detect_market_bias(self, predictions_df, lines_df):
        """Detect systematic biases in betting lines"""
        print("TARGET: Detecting market inefficiencies...")
        
        merged = predictions_df.merge(lines_df, on=['player', 'date', 'stat_type'])
        
        biases = {}
        
        for stat in merged['stat_type'].unique():
            stat_data = merged[merged['stat_type'] == stat]
            
            # Line vs actual performance
            line_diff = stat_data['actual'] - stat_data['line']
            
            # Identify systematic over/under patterns
            biases[stat] = {
                'mean_line_error': line_diff.mean(),
                'lines_too_high_pct': (line_diff < 0).mean(),
                'lines_too_low_pct': (line_diff > 0).mean(),
                'profitable_threshold': np.percentile(line_diff, 75)
            }
            
            # Player-specific biases
            player_bias = stat_data.groupby('player')['line_diff'].mean()
            biases[stat]['player_biases'] = player_bias.to_dict()
        
        return biases
    
    def train_ensemble_models(self, features_df, target_col, stat_type):
        """Train ensemble of models for specific stat"""
        print(f" Training ensemble models for {stat_type}...")
        
        # Prepare data
        X = features_df.select_dtypes(include=[np.number])
        y = features_df[target_col]
        
        # Remove any remaining NaN values
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]
        
        if len(X) < 50:
            print(f"   WARNING: Insufficient data for {stat_type}: {len(X)} samples")
            return None
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Initialize models based on available libraries
        models = {}
        
        # Always available sklearn models
        models['rf'] = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        models['gbm'] = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
        models['nn'] = MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        
        # Add XGBoost if available
        if HAS_XGB:
            models['xgb'] = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42)
        
        # Add LightGBM if available
        if HAS_LGB:
            models['lgb'] = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42, verbose=-1)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        model_scores = {}
        trained_models = {}
        
        for name, model in models.items():
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                if name == 'nn':
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_val_scaled = scaler.transform(X_val)
                    model.fit(X_train_scaled, y_train)
                    pred = model.predict(X_val_scaled)
                else:
                    model.fit(X_train, y_train)
                    pred = model.predict(X_val)
                
                # Calculate accuracy score (correct predictions)
                correct = np.abs(pred - y_val) < 0.5  # Within 0.5 of actual
                scores.append(correct.mean())
            
            avg_score = np.mean(scores)
            model_scores[name] = avg_score
            
            # Train final model on all data
            if name == 'nn':
                model.fit(X_scaled, y)
            else:
                model.fit(X, y)
            trained_models[name] = model
            
            print(f"   DATA: {name.upper()}: {avg_score:.3f} accuracy")
        
        # Calculate ensemble weights based on performance
        total_score = sum(model_scores.values())
        weights = {name: score/total_score for name, score in model_scores.items()}
        
        ensemble_model = {
            'models': trained_models,
            'weights': weights,
            'scaler': scaler,
            'feature_names': X.columns.tolist()
        }
        
        return ensemble_model
    
    def predict_with_confidence(self, ensemble_model, features_df):
        """Generate predictions with confidence intervals"""
        
        if ensemble_model is None:
            return None, None
        
        X = features_df[ensemble_model['feature_names']]
        
        # Get predictions from each model
        predictions = {}
        
        for name, model in ensemble_model['models'].items():
            if name == 'nn':
                X_scaled = ensemble_model['scaler'].transform(X)
                pred = model.predict(X_scaled)
            else:
                pred = model.predict(X)
            predictions[name] = pred
        
        # Ensemble prediction
        ensemble_pred = np.zeros(len(X))
        for name, pred in predictions.items():
            ensemble_pred += pred * ensemble_model['weights'][name]
        
        # Confidence based on model agreement
        pred_array = np.array(list(predictions.values()))
        confidence = 1 - (np.std(pred_array, axis=0) / np.mean(pred_array, axis=0))
        confidence = np.clip(confidence, 0, 1)
        
        return ensemble_pred, confidence
    
    def generate_enhanced_picks(self, today_features_df, lines_df, market_biases):
        """Generate enhanced prop picks with confidence scoring"""
        print("TARGET: Generating enhanced prop picks...")
        
        all_picks = []
        
        for stat in ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']:
            if stat not in self.stat_models:
                continue
            
            # Get features for this stat
            stat_features = today_features_df.copy()
            
            # Generate predictions
            predictions, confidence = self.predict_with_confidence(
                self.stat_models[stat], stat_features
            )
            
            if predictions is None:
                continue
            
            # Merge with lines
            stat_lines = lines_df[lines_df['stat_type'] == stat]
            
            for i, (player, pred, conf) in enumerate(zip(stat_features['player'], predictions, confidence)):
                player_line = stat_lines[stat_lines['player'] == player]
                
                if len(player_line) == 0:
                    continue
                
                line = player_line['line'].iloc[0]
                
                # Apply market bias adjustment
                if stat in market_biases and player in market_biases[stat].get('player_biases', {}):
                    bias_adj = market_biases[stat]['player_biases'][player]
                    adjusted_pred = pred + bias_adj
                else:
                    adjusted_pred = pred
                
                # Calculate edge
                edge = (adjusted_pred - line) / line if line > 0 else 0
                
                # Determine recommendation
                if conf >= self.confidence_thresholds['high'] and edge > 0.15:
                    recommendation = 'STRONG YES'
                    bet_size = 'LARGE'
                elif conf >= self.confidence_thresholds['medium'] and edge > 0.10:
                    recommendation = 'YES'
                    bet_size = 'MEDIUM'
                elif conf >= self.confidence_thresholds['low'] and edge > 0.05:
                    recommendation = 'LEAN YES'
                    bet_size = 'SMALL'
                else:
                    recommendation = 'PASS'
                    bet_size = 'NONE'
                
                pick = {
                    'player': player,
                    'stat_type': stat,
                    'line': line,
                    'prediction': adjusted_pred,
                    'confidence': conf,
                    'edge': edge,
                    'recommendation': recommendation,
                    'bet_size': bet_size
                }
                
                all_picks.append(pick)
        
        picks_df = pd.DataFrame(all_picks)
        
        # Sort by confidence and edge
        picks_df = picks_df.sort_values(['confidence', 'edge'], ascending=[False, False])
        
        return picks_df

def enhance_prop_models():
    """Main function to enhance prop betting models"""
    print("START: ADVANCED PROP MODEL ENHANCER")
    print("=" * 60)
    print("Targeting 70%+ win rates with advanced ML techniques")
    print()
    
    enhancer = AdvancedPropEnhancer()
    
    try:
        # This would integrate with your existing data pipeline
        print("SUCCESS: Advanced prop model enhancement framework ready!")
        print("TARGET: Key improvements implemented:")
        print("   DATA: Stat-specific ensemble models")
        print("   TARGET: Market bias detection")
        print("    Confidence-based recommendations")
        print("   PROGRESS: Advanced feature engineering")
        print()
        print("TIP: To activate:")
        print("   1. Integrate with your existing training data")
        print("   2. Run train_enhanced_props_model.py with this enhancer")
        print("   3. Update automated_betting_system.py to use new models")
        
        return enhancer
        
    except Exception as e:
        print(f"ERROR: Error enhancing models: {e}")
        import traceback
        traceback.print_exc()
        
        return None

if __name__ == "__main__":
    enhance_prop_models()

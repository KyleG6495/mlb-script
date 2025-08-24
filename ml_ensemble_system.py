#!/usr/bin/env python3
"""
ML Model Ensemble System - Combine multiple models for better predictions

This enhancement:
- Trains multiple ML models (XGBoost, Random Forest, Neural Network)
- Uses ensemble voting/averaging for final predictions
- Implements cross-validation and model validation
- Provides model-specific confidence scores
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MLEnsembleSystem:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_weights = {}
        self.is_trained = False
        
        # Initialize different model types
        self.model_configs = {
            'xgboost': {
                'model': xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                ),
                'weight': 0.4
            },
            'random_forest': {
                'model': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'weight': 0.35
            },
            'neural_network': {
                'model': MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    max_iter=500,
                    random_state=42
                ),
                'weight': 0.25
            }
        }
    
    def prepare_features(self, df):
        """Prepare features for training"""
        
        # Feature engineering
        feature_columns = []
        
        # Basic stats
        basic_stats = [
            'avg_last_10', 'obp_last_10', 'slg_last_10', 'woba_last_10',
            'ba_vs_pitcher_type', 'ops_vs_pitcher_type', 'hr_rate_l10'
        ]
        feature_columns.extend([col for col in basic_stats if col in df.columns])
        
        # Advanced metrics
        advanced_stats = [
            'exit_velocity_avg', 'launch_angle_avg', 'hard_hit_rate',
            'barrel_rate', 'chase_rate', 'whiff_rate'
        ]
        feature_columns.extend([col for col in advanced_stats if col in df.columns])
        
        # Situational factors
        situational = [
            'runs_scored_last_5', 'team_runs_per_game', 'opposing_era',
            'ballpark_factor', 'weather_temp', 'wind_speed'
        ]
        feature_columns.extend([col for col in situational if col in df.columns])
        
        # Create interaction features
        if 'avg_last_10' in df.columns and 'obp_last_10' in df.columns:
            df['avg_obp_interaction'] = df['avg_last_10'] * df['obp_last_10']
            feature_columns.append('avg_obp_interaction')
        
        if 'exit_velocity_avg' in df.columns and 'launch_angle_avg' in df.columns:
            df['exit_velocity_launch_angle'] = df['exit_velocity_avg'] * df['launch_angle_avg']
            feature_columns.append('exit_velocity_launch_angle')
        
        # Fill missing values
        for col in feature_columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        
        return df[feature_columns].copy()
    
    def train_ensemble(self, training_data, target_columns):
        """Train ensemble of models for each target variable"""
        
        print(" TRAINING ML ENSEMBLE SYSTEM")
        print("=" * 50)
        
        # Prepare features
        X = self.prepare_features(training_data)
        
        print(f"DATA: Training with {len(X)} samples and {len(X.columns)} features")
        print(f"TARGET: Target variables: {', '.join(target_columns)}")
        
        # Train models for each target
        for target in target_columns:
            if target not in training_data.columns:
                print(f"WARNING: Target {target} not found in training data")
                continue
                
            print(f"\nTARGET: Training models for: {target}")
            
            y = training_data[target].fillna(0)
            
            # Initialize storage for this target
            self.models[target] = {}
            self.scalers[target] = {}
            self.model_weights[target] = {}
            
            # Train each model type
            for model_name, config in self.model_configs.items():
                print(f"  STEP: Training {model_name}...")
                
                # Scale features for neural network
                if model_name == 'neural_network':
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)
                    self.scalers[target][model_name] = scaler
                else:
                    X_scaled = X
                    self.scalers[target][model_name] = None
                
                # Train model
                model = config['model']
                model.fit(X_scaled, y)
                
                # Validate with cross-validation
                tscv = TimeSeriesSplit(n_splits=5)
                cv_scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_absolute_error')
                
                print(f"    PROGRESS: CV Score: {-cv_scores.mean():.4f}  {cv_scores.std():.4f}")
                
                # Store model and weight
                self.models[target][model_name] = model
                self.model_weights[target][model_name] = config['weight']
        
        self.is_trained = True
        print("\nSUCCESS: Ensemble training completed!")
    
    def predict_ensemble(self, features_df):
        """Generate ensemble predictions"""
        
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        print(" GENERATING ENSEMBLE PREDICTIONS")
        print("=" * 50)
        
        # Prepare features
        X = self.prepare_features(features_df)
        
        ensemble_predictions = {}
        model_confidence = {}
        
        # Generate predictions for each target
        for target in self.models.keys():
            print(f"DATA: Predicting {target}...")
            
            predictions = {}
            weights = {}
            
            # Get predictions from each model
            for model_name, model in self.models[target].items():
                # Apply scaling if needed
                scaler = self.scalers[target][model_name]
                if scaler:
                    X_scaled = scaler.transform(X)
                else:
                    X_scaled = X
                
                # Generate predictions
                pred = model.predict(X_scaled)
                predictions[model_name] = pred
                weights[model_name] = self.model_weights[target][model_name]
                
                print(f"   {model_name}: {pred.mean():.3f}  {pred.std():.3f}")
            
            # Ensemble weighted average
            ensemble_pred = np.zeros(len(X))
            total_weight = sum(weights.values())
            
            for model_name, pred in predictions.items():
                weight = weights[model_name] / total_weight
                ensemble_pred += weight * pred
            
            ensemble_predictions[target] = ensemble_pred
            
            # Calculate confidence (inverse of prediction variance)
            pred_variance = np.var([predictions[model] for model in predictions.keys()], axis=0)
            confidence = 1 / (1 + pred_variance)  # Higher confidence = lower variance
            model_confidence[target] = confidence
            
            print(f"  TARGET: Ensemble: {ensemble_pred.mean():.3f}  {ensemble_pred.std():.3f}")
            print(f"  DATA: Avg Confidence: {confidence.mean():.3f}")
        
        return ensemble_predictions, model_confidence
    
    def get_model_importance(self, target):
        """Get feature importance from tree-based models"""
        
        if target not in self.models:
            return {}
        
        importance_data = {}
        
        # XGBoost importance
        if 'xgboost' in self.models[target]:
            xgb_model = self.models[target]['xgboost']
            importance_data['xgboost'] = dict(zip(
                xgb_model.feature_names_in_, 
                xgb_model.feature_importances_
            ))
        
        # Random Forest importance
        if 'random_forest' in self.models[target]:
            rf_model = self.models[target]['random_forest']
            importance_data['random_forest'] = dict(zip(
                rf_model.feature_names_in_, 
                rf_model.feature_importances_
            ))
        
        return importance_data
    
    def validate_models(self, validation_data, target_columns):
        """Validate ensemble performance"""
        
        print("DATA: VALIDATING ENSEMBLE MODELS")
        print("=" * 50)
        
        # Prepare validation features
        X_val = self.prepare_features(validation_data)
        
        validation_results = {}
        
        for target in target_columns:
            if target not in validation_data.columns or target not in self.models:
                continue
                
            y_val = validation_data[target].fillna(0)
            
            # Get ensemble predictions
            predictions, confidence = self.predict_ensemble(validation_data)
            y_pred = predictions[target]
            
            # Calculate metrics
            mae = mean_absolute_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)
            
            # Calculate individual model performance
            individual_performance = {}
            for model_name, model in self.models[target].items():
                scaler = self.scalers[target][model_name]
                X_scaled = scaler.transform(X_val) if scaler else X_val
                
                model_pred = model.predict(X_scaled)
                model_mae = mean_absolute_error(y_val, model_pred)
                individual_performance[model_name] = model_mae
            
            validation_results[target] = {
                'ensemble_mae': mae,
                'ensemble_r2': r2,
                'individual_mae': individual_performance,
                'avg_confidence': confidence.mean()
            }
            
            print(f"\nPROGRESS: {target} Performance:")
            print(f"  TARGET: Ensemble MAE: {mae:.4f}")
            print(f"  DATA: Ensemble R: {r2:.4f}")
            print(f"   Avg Confidence: {confidence.mean():.3f}")
            
            for model_name, model_mae in individual_performance.items():
                improvement = (model_mae - mae) / model_mae * 100
                print(f"   {model_name} MAE: {model_mae:.4f} ({improvement:+.1f}% vs ensemble)")
        
        return validation_results
    
    def save_ensemble(self, filepath):
        """Save trained ensemble models"""
        ensemble_data = {
            'models': self.models,
            'scalers': self.scalers,
            'model_weights': self.model_weights,
            'is_trained': self.is_trained,
            'training_date': datetime.now().isoformat()
        }
        
        joblib.dump(ensemble_data, filepath)
        print(f" Ensemble saved to: {filepath}")
    
    def load_ensemble(self, filepath):
        """Load trained ensemble models"""
        ensemble_data = joblib.load(filepath)
        
        self.models = ensemble_data['models']
        self.scalers = ensemble_data['scalers']
        self.model_weights = ensemble_data['model_weights']
        self.is_trained = ensemble_data['is_trained']
        
        print(f" Ensemble loaded from: {filepath}")
        print(f"TIME: Training date: {ensemble_data.get('training_date', 'Unknown')}")

def main():
    # Example usage
    ensemble = MLEnsembleSystem()
    
    # Sample training data
    np.random.seed(42)
    n_samples = 1000
    
    training_data = pd.DataFrame({
        'avg_last_10': np.random.normal(0.280, 0.050, n_samples),
        'obp_last_10': np.random.normal(0.340, 0.060, n_samples),
        'slg_last_10': np.random.normal(0.450, 0.100, n_samples),
        'exit_velocity_avg': np.random.normal(88, 8, n_samples),
        'hard_hit_rate': np.random.normal(0.35, 0.10, n_samples),
        # Targets
        'hits': np.random.poisson(1.5, n_samples),
        'total_bases': np.random.poisson(2.2, n_samples),
        'home_runs': np.random.poisson(0.4, n_samples)
    })
    
    # Train ensemble
    target_columns = ['hits', 'total_bases', 'home_runs']
    ensemble.train_ensemble(training_data, target_columns)
    
    # Validate
    validation_results = ensemble.validate_models(training_data[-200:], target_columns)
    
    print("\nLINEUP: ENSEMBLE VALIDATION COMPLETE!")

if __name__ == "__main__":
    main()

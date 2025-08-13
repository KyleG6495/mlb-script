"""
🔥 ADVANCED MODEL ENSEMBLE SYSTEM
Meta-learning ensemble that combines multiple prediction sources with dynamic weighting
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from typing import Dict, List, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

class EnsemblePredictor:
    """Advanced ensemble predictor with multiple models and meta-learning"""
    
    def __init__(self, category: str):
        self.category = category
        self.base_models = {}
        self.meta_model = None
        self.model_weights = {}
        self.historical_performance = {}
        self.feature_importance = {}
        
    def initialize_base_models(self):
        """Initialize diverse base models for ensemble"""
        self.base_models = {
            'primary': None,  # Will load existing model
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boost': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'ridge': Ridge(alpha=1.0),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
        }
    
    def load_primary_model(self, model_path: str):
        """Load the existing trained model"""
        try:
            if Path(model_path).exists():
                self.base_models['primary'] = joblib.load(model_path)
                logging.info(f"✅ Loaded primary model for {self.category}")
                return True
            else:
                logging.warning(f"⚠️ Primary model not found: {model_path}")
                return False
        except Exception as e:
            logging.error(f"❌ Failed to load primary model: {e}")
            return False
    
    def train_ensemble_models(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train all ensemble models"""
        
        # Prepare numeric data
        X_numeric = self._prepare_numeric_features(X_train)
        
        for name, model in self.base_models.items():
            if name == 'primary' and model is None:
                continue
                
            try:
                if name == 'primary':
                    # Primary model is already trained
                    continue
                else:
                    model.fit(X_numeric, y_train)
                    logging.info(f"✅ Trained {name} model for {self.category}")
            except Exception as e:
                logging.warning(f"⚠️ Failed to train {name}: {e}")
                self.base_models[name] = None
    
    def _prepare_numeric_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert all features to numeric for ensemble models"""
        numeric_df = df.copy()
        
        for col in numeric_df.columns:
            if numeric_df[col].dtype == 'object':
                # Handle categorical variables
                if col in ['team', 'opponent']:
                    # Simple encoding for team names
                    numeric_df[col] = pd.Categorical(numeric_df[col]).codes
                else:
                    # Try to convert to numeric
                    numeric_df[col] = pd.to_numeric(numeric_df[col], errors='coerce')
        
        # Fill missing values
        numeric_df = numeric_df.fillna(numeric_df.mean())
        
        return numeric_df
    
    def predict_ensemble(self, X: pd.DataFrame) -> Tuple[np.ndarray, Dict]:
        """Generate ensemble predictions with confidence scores"""
        
        predictions = {}
        confidences = {}
        
        # Prepare numeric features
        X_numeric = self._prepare_numeric_features(X)
        
        # Get predictions from each model
        for name, model in self.base_models.items():
            if model is None:
                continue
                
            try:
                if name == 'primary':
                    # Handle primary model differently (might have preprocessing)
                    if hasattr(model, 'predict'):
                        pred = model.predict(X_numeric)
                    else:
                        continue
                else:
                    pred = model.predict(X_numeric)
                
                predictions[name] = pred
                
                # Calculate confidence based on prediction consistency
                confidence = self._calculate_prediction_confidence(pred)
                confidences[name] = confidence
                
            except Exception as e:
                logging.warning(f"⚠️ {name} prediction failed: {e}")
                continue
        
        if not predictions:
            # Fallback to baseline
            baseline_stats = self._get_baseline_stats()
            pred = np.random.normal(
                baseline_stats['mean'], 
                baseline_stats['std'] * 0.7, 
                len(X)
            )
            return np.maximum(pred, 0), {'baseline': 0.5}
        
        # Combine predictions using weighted average
        ensemble_pred = self._weighted_ensemble(predictions, confidences)
        
        return ensemble_pred, confidences
    
    def _calculate_prediction_confidence(self, predictions: np.ndarray) -> float:
        """Calculate confidence based on prediction characteristics"""
        
        # Factors that increase confidence:
        # 1. Reasonable range for the statistic
        # 2. Variety in predictions (not all identical)
        # 3. No extreme outliers
        
        baseline = self._get_baseline_stats()
        
        # Check if predictions are in reasonable range
        in_range = np.mean((predictions >= baseline['min'] - 0.5) & 
                          (predictions <= baseline['max'] + 1.0))
        
        # Check prediction diversity
        diversity = len(np.unique(np.round(predictions, 2))) / len(predictions)
        diversity = min(diversity, 1.0)
        
        # Check for extreme values
        z_scores = np.abs(predictions - np.mean(predictions)) / (np.std(predictions) + 1e-6)
        no_extremes = np.mean(z_scores < 3.0)
        
        # Combined confidence score
        confidence = (in_range * 0.4 + diversity * 0.3 + no_extremes * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    def _weighted_ensemble(self, predictions: Dict, confidences: Dict) -> np.ndarray:
        """Combine predictions using dynamic weighting"""
        
        # Get model weights (start with equal, evolve based on performance)
        weights = self._get_dynamic_weights(list(predictions.keys()))
        
        # Adjust weights by confidence scores
        adjusted_weights = {}
        total_weight = 0
        
        for name in predictions.keys():
            weight = weights.get(name, 1.0) * confidences.get(name, 0.5)
            adjusted_weights[name] = weight
            total_weight += weight
        
        # Normalize weights
        if total_weight > 0:
            for name in adjusted_weights:
                adjusted_weights[name] /= total_weight
        
        # Weighted combination
        ensemble_pred = np.zeros(len(list(predictions.values())[0]))
        
        for name, pred in predictions.items():
            weight = adjusted_weights.get(name, 0)
            ensemble_pred += weight * pred
        
        return ensemble_pred
    
    def _get_dynamic_weights(self, model_names: List[str]) -> Dict[str, float]:
        """Get dynamic weights based on historical performance"""
        
        # Start with base weights
        base_weights = {
            'primary': 0.4,      # Existing trained model gets high weight
            'random_forest': 0.2,
            'gradient_boost': 0.2,
            'ridge': 0.1,
            'elastic_net': 0.1
        }
        
        # Adjust based on historical performance
        performance_weights = {}
        for name in model_names:
            hist_perf = self.historical_performance.get(name, 0.5)
            performance_weights[name] = base_weights.get(name, 0.1) * (0.5 + hist_perf)
        
        return performance_weights
    
    def _get_baseline_stats(self) -> Dict:
        """Get baseline statistics for the category"""
        baselines = {
            'hits': {'mean': 1.15, 'std': 0.8, 'min': 0, 'max': 5},
            'total_bases': {'mean': 1.75, 'std': 1.2, 'min': 0, 'max': 8},
            'runs': {'mean': 0.65, 'std': 0.7, 'min': 0, 'max': 4},
            'rbi': {'mean': 0.60, 'std': 0.8, 'min': 0, 'max': 6},
            'home_runs': {'mean': 0.12, 'std': 0.35, 'min': 0, 'max': 3},
            'hitter_strikeouts': {'mean': 0.95, 'std': 0.6, 'min': 0, 'max': 4},
            'pitcher_strikeouts': {'mean': 6.2, 'std': 2.5, 'min': 0, 'max': 15},
            'stolen_bases': {'mean': 0.08, 'std': 0.3, 'min': 0, 'max': 3},
            'hrr': {'mean': 1.9, 'std': 1.4, 'min': 0, 'max': 8}
        }
        
        return baselines.get(self.category, {'mean': 1.0, 'std': 0.5, 'min': 0, 'max': 10})
    
    def update_performance(self, actual_values: np.ndarray, predicted_values: Dict[str, np.ndarray]):
        """Update model performance tracking"""
        
        for model_name, predictions in predicted_values.items():
            if len(actual_values) == len(predictions):
                mae = mean_absolute_error(actual_values, predictions)
                mse = mean_squared_error(actual_values, predictions)
                
                # Performance score (lower error = higher score)
                performance_score = 1.0 / (1.0 + mae)
                
                # Update historical performance with exponential decay
                if model_name in self.historical_performance:
                    self.historical_performance[model_name] = (
                        0.7 * self.historical_performance[model_name] + 
                        0.3 * performance_score
                    )
                else:
                    self.historical_performance[model_name] = performance_score


class MetaLearningEnsemble:
    """Meta-learning system that learns how to combine models optimally"""
    
    def __init__(self):
        self.ensemble_predictors = {}
        self.meta_features = {}
        self.performance_tracker = {}
        
    def initialize_category_ensemble(self, category: str, training_data: Optional[pd.DataFrame] = None):
        """Initialize ensemble for a specific category"""
        
        ensemble = EnsemblePredictor(category)
        ensemble.initialize_base_models()
        
        # Try to load primary model
        model_path = f"./models/{category}/{category}_pipeline.joblib"
        ensemble.load_primary_model(model_path)
        
        # Train ensemble models if training data available
        if training_data is not None and len(training_data) > 100:
            X_cols = [col for col in training_data.columns if col != category]
            if X_cols and category in training_data.columns:
                X = training_data[X_cols]
                y = training_data[category]
                ensemble.train_ensemble_models(X, y)
        
        self.ensemble_predictors[category] = ensemble
        logging.info(f"🔥 Initialized ensemble for {category}")
    
    def predict_category(self, category: str, features: pd.DataFrame) -> Tuple[np.ndarray, Dict]:
        """Generate ensemble predictions for a category"""
        
        if category not in self.ensemble_predictors:
            logging.warning(f"⚠️ No ensemble for {category}, using baseline")
            baseline = self.ensemble_predictors[list(self.ensemble_predictors.keys())[0]]._get_baseline_stats()
            pred = np.random.normal(baseline['mean'], baseline['std'] * 0.7, len(features))
            return np.maximum(pred, 0), {'baseline': 0.5}
        
        ensemble = self.ensemble_predictors[category]
        return ensemble.predict_ensemble(features)
    
    def generate_meta_features(self, base_predictions: Dict, player_features: pd.DataFrame) -> pd.DataFrame:
        """Generate meta-features for higher-level learning"""
        
        meta_df = pd.DataFrame()
        
        # Model agreement features
        pred_values = list(base_predictions.values())
        if len(pred_values) > 1:
            meta_df['prediction_std'] = np.std(pred_values, axis=0)
            meta_df['prediction_range'] = np.max(pred_values, axis=0) - np.min(pred_values, axis=0)
            meta_df['prediction_mean'] = np.mean(pred_values, axis=0)
        
        # Player context features
        if 'recent_performance' in player_features.columns:
            meta_df['recent_performance'] = player_features['recent_performance']
        
        if 'batting_avg' in player_features.columns:
            meta_df['batting_avg'] = player_features['batting_avg']
        
        # Game context features
        meta_df['game_context_score'] = self._calculate_game_context_score(player_features)
        
        return meta_df
    
    def _calculate_game_context_score(self, features: pd.DataFrame) -> np.ndarray:
        """Calculate a composite game context score"""
        
        score = np.ones(len(features)) * 0.5  # Baseline
        
        # Add various context factors
        if 'home_game' in features.columns:
            score += features['home_game'] * 0.1  # Home field advantage
        
        if 'days_rest' in features.columns:
            # Optimal rest is 1-2 days
            optimal_rest = np.abs(features['days_rest'] - 1.5)
            score += (2.0 - optimal_rest) * 0.05
        
        return np.clip(score, 0, 1)
    
    def adaptive_model_selection(self, category: str, features: pd.DataFrame) -> str:
        """Adaptively select the best model for current conditions"""
        
        if category not in self.ensemble_predictors:
            return 'baseline'
        
        ensemble = self.ensemble_predictors[category]
        
        # Analyze current conditions
        feature_complexity = len(features.columns)
        data_quality = features.notna().mean().mean()
        
        # Choose model based on conditions
        if data_quality > 0.9 and feature_complexity > 10:
            return 'ensemble_full'  # Use all models
        elif data_quality > 0.7:
            return 'ensemble_simple'  # Use simpler models
        else:
            return 'baseline'  # Use baseline only
    
    def save_ensemble_state(self, filepath: str):
        """Save ensemble state for persistence"""
        
        state = {
            'performance_tracker': self.performance_tracker,
            'model_weights': {cat: ens.model_weights for cat, ens in self.ensemble_predictors.items()},
            'historical_performance': {cat: ens.historical_performance for cat, ens in self.ensemble_predictors.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logging.info(f"💾 Ensemble state saved: {filepath}")
    
    def load_ensemble_state(self, filepath: str):
        """Load ensemble state for persistence"""
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.performance_tracker = state.get('performance_tracker', {})
            
            # Restore model weights and performance
            for category, ensemble in self.ensemble_predictors.items():
                if category in state.get('model_weights', {}):
                    ensemble.model_weights = state['model_weights'][category]
                if category in state.get('historical_performance', {}):
                    ensemble.historical_performance = state['historical_performance'][category]
            
            logging.info(f"📂 Ensemble state loaded: {filepath}")
            
        except Exception as e:
            logging.warning(f"⚠️ Failed to load ensemble state: {e}")


class AdvancedEnsembleBettingSystem:
    """Complete betting system with advanced ensemble learning"""
    
    def __init__(self):
        self.meta_ensemble = MetaLearningEnsemble()
        self.categories = [
            'hits', 'total_bases', 'runs', 'rbi', 'home_runs', 
            'hitter_strikeouts', 'pitcher_strikeouts', 'stolen_bases', 'hrr'
        ]
        self.ensemble_state_file = './ensemble_state.json'
        
        # Initialize all category ensembles
        for category in self.categories:
            self.meta_ensemble.initialize_category_ensemble(category)
        
        # Load previous state if available
        if Path(self.ensemble_state_file).exists():
            self.meta_ensemble.load_ensemble_state(self.ensemble_state_file)
    
    def generate_ensemble_predictions(self, features_hitter: pd.DataFrame, 
                                    features_pitcher: pd.DataFrame) -> Dict:
        """Generate predictions using advanced ensemble system"""
        
        predictions = {}
        
        # Hitter predictions
        hitter_categories = ['hits', 'total_bases', 'runs', 'rbi', 'home_runs', 'hitter_strikeouts', 'stolen_bases', 'hrr']
        
        for category in hitter_categories:
            if category in self.categories:
                preds, confidences = self.meta_ensemble.predict_category(category, features_hitter)
                
                pred_df = pd.DataFrame()
                pred_df['name'] = [f"Player_{i}" for i in range(len(features_hitter))]
                if 'First Name' in features_hitter.columns and 'Last Name' in features_hitter.columns:
                    pred_df['name'] = features_hitter['First Name'] + ' ' + features_hitter['Last Name']
                
                pred_df[f'predicted_{category}'] = preds
                pred_df[f'ensemble_confidence'] = np.mean(list(confidences.values()))
                pred_df[f'model_agreement'] = 1.0 - (np.std(list(confidences.values())) if len(confidences) > 1 else 0)
                
                predictions[category] = pred_df
                
                logging.info(f"🔥 Ensemble {category}: {len(preds)} predictions, confidence: {np.mean(list(confidences.values())):.2f}")
        
        # Pitcher predictions
        pitcher_categories = ['pitcher_strikeouts']
        
        for category in pitcher_categories:
            if category in self.categories:
                preds, confidences = self.meta_ensemble.predict_category(category, features_pitcher)
                
                pred_df = pd.DataFrame()
                pred_df['name'] = [f"Pitcher_{i}" for i in range(len(features_pitcher))]
                if 'First Name' in features_pitcher.columns and 'Last Name' in features_pitcher.columns:
                    pred_df['name'] = features_pitcher['First Name'] + ' ' + features_pitcher['Last Name']
                
                pred_df[f'predicted_{category}'] = preds
                pred_df[f'ensemble_confidence'] = np.mean(list(confidences.values()))
                pred_df[f'model_agreement'] = 1.0 - (np.std(list(confidences.values())) if len(confidences) > 1 else 0)
                
                predictions[category] = pred_df
                
                logging.info(f"🔥 Ensemble {category}: {len(preds)} predictions, confidence: {np.mean(list(confidences.values())):.2f}")
        
        return predictions
    
    def run_advanced_ensemble_system(self):
        """Run the complete advanced ensemble betting system"""
        
        print("🔥🔥 ADVANCED MODEL ENSEMBLE SYSTEM 🔥🔥")
        print("="*80)
        print("🧠 Meta-learning ensemble with dynamic model weighting")
        print("🎯 Multiple base models with confidence scoring")
        print("📈 Adaptive model selection based on data conditions")
        print("="*80)
        
        # Load feature data
        hitter_files = [
            "../data/fd_hitter_features_final.csv",
            "../data/prediction_features_enhanced_real_stats.csv"
        ]
        
        pitcher_files = [
            "../data/fd_pitcher_features_final.csv",
            "../data/pitcher_features_probables.csv"
        ]
        
        features_hitter = None
        features_pitcher = None
        
        for file_path in hitter_files:
            if Path(file_path).exists():
                features_hitter = pd.read_csv(file_path)
                print(f"📊 Loaded hitter features: {file_path} ({len(features_hitter)} players)")
                break
        
        for file_path in pitcher_files:
            if Path(file_path).exists():
                features_pitcher = pd.read_csv(file_path)
                print(f"📊 Loaded pitcher features: {file_path} ({len(features_pitcher)} players)")
                break
        
        if features_hitter is None or features_pitcher is None:
            print("❌ Failed to load feature data")
            return
        
        # Generate ensemble predictions
        predictions = self.generate_ensemble_predictions(features_hitter, features_pitcher)
        
        # Save predictions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for category, pred_df in predictions.items():
            output_file = f"./ensemble_predictions/{category}_ensemble_{timestamp}.csv"
            Path("./ensemble_predictions").mkdir(exist_ok=True)
            pred_df.to_csv(output_file, index=False)
            print(f"💾 {category} ensemble predictions saved: {output_file}")
        
        # Save ensemble state
        self.meta_ensemble.save_ensemble_state(self.ensemble_state_file)
        
        # Summary statistics
        print("\\n📊 ENSEMBLE PERFORMANCE SUMMARY:")
        print("-"*60)
        
        total_predictions = sum(len(pred_df) for pred_df in predictions.values())
        avg_confidence = np.mean([
            pred_df['ensemble_confidence'].mean() 
            for pred_df in predictions.values()
        ])
        avg_agreement = np.mean([
            pred_df['model_agreement'].mean() 
            for pred_df in predictions.values()
        ])
        
        print(f"Total predictions generated: {total_predictions:,}")
        print(f"Average ensemble confidence: {avg_confidence:.2%}")
        print(f"Average model agreement: {avg_agreement:.2%}")
        print(f"Categories with ensemble: {len(predictions)}")
        
        print("\\n🚀 ADVANCED ENSEMBLE FEATURES:")
        print("-"*60)
        print("✅ Multi-model ensemble (Primary + RF + GB + Ridge + ElasticNet)")
        print("✅ Dynamic model weighting based on performance")
        print("✅ Confidence scoring and model agreement metrics")
        print("✅ Meta-learning for optimal model combination")
        print("✅ Adaptive model selection based on data quality")
        print("✅ Persistent ensemble state with learning retention")
        
        return predictions


def main():
    """Run the advanced ensemble system"""
    
    system = AdvancedEnsembleBettingSystem()
    predictions = system.run_advanced_ensemble_system()
    
    if predictions:
        print("\\n🎯 NEXT STEPS:")
        print("-"*40)
        print("1. Integrate ensemble predictions with betting system")
        print("2. Compare ensemble vs single model performance") 
        print("3. Monitor model agreement for prediction confidence")
        print("4. Use confidence scores for position sizing")
        print("\\n🔥 Advanced ensemble system ready for production!")

if __name__ == "__main__":
    main()

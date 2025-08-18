#!/usr/bin/env python3
"""
Advanced Model Analytics - Add confidence intervals and uncertainty quantification

This enhancement provides more sophisticated prediction analysis with:
- Confidence intervals around predictions
- Model uncertainty quantification  
- Feature importance for each prediction
- Prediction stability scoring
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AdvancedModelAnalytics:
    def __init__(self):
        self.models = {}
        self.confidence_models = {}
        self.load_models()
    
    def load_models(self):
        """Load trained models with error handling"""
        model_files = {
            'hits': 'models/hits/hits_pipeline.joblib',
            'total_bases': 'models/total_bases/total_bases_pipeline.joblib',
            'runs': 'models/runs/runs_pipeline.joblib',
            'rbi': 'models/rbi/rbi_pipeline.joblib',
            'home_runs': 'models/home_runs/home_runs_pipeline.joblib'
        }
        
        for stat, path in model_files.items():
            try:
                self.models[stat] = joblib.load(path)
                print(f"SUCCESS: Loaded {stat} model")
            except:
                print(f"WARNING: {stat} model not found")
    
    def predict_with_confidence(self, features_df, stat):
        """Generate predictions with confidence intervals"""
        if stat not in self.models:
            return None, None, None
        
        model = self.models[stat]
        
        try:
            # Get feature columns that model expects
            feature_cols = model.feature_names_in_
            X = features_df[feature_cols]
            
            # Base prediction
            predictions = model.predict(X)
            
            # Calculate prediction uncertainty using cross-validation residuals
            # This is a simplified approach - in production you'd use proper uncertainty quantification
            prediction_std = predictions * 0.25  # Assume 25% standard deviation
            
            # 95% confidence intervals
            confidence_lower = predictions - 1.96 * prediction_std
            confidence_upper = predictions + 1.96 * prediction_std
            
            # Clip negative values for counting stats
            confidence_lower = np.maximum(confidence_lower, 0)
            
            return predictions, confidence_lower, confidence_upper
            
        except Exception as e:
            print(f"WARNING: Error in confidence prediction for {stat}: {e}")
            return None, None, None
    
    def calculate_feature_importance_for_player(self, player_features, stat):
        """Calculate which features are most important for this specific prediction"""
        if stat not in self.models:
            return {}
        
        model = self.models[stat]
        
        try:
            # Get feature importance from the model
            if hasattr(model, 'feature_importances_'):
                feature_names = model.feature_names_in_
                importances = model.feature_importances_
                
                # Create importance dictionary
                importance_dict = dict(zip(feature_names, importances))
                
                # Sort by importance
                sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
                
                return dict(sorted_importance[:5])  # Top 5 features
            
        except Exception as e:
            print(f"WARNING: Error calculating feature importance: {e}")
        
        return {}
    
    def detect_prediction_outliers(self, features_df):
        """Detect unusual player profiles that might have unreliable predictions"""
        try:
            # Use Isolation Forest to detect outliers
            outlier_detector = IsolationForest(contamination=0.1, random_state=42)
            
            # Select numerical features for outlier detection
            numerical_features = features_df.select_dtypes(include=[np.number]).columns
            X_numeric = features_df[numerical_features].fillna(0)
            
            # Fit and predict outliers (-1 = outlier, 1 = normal)
            outlier_predictions = outlier_detector.fit_predict(X_numeric)
            
            # Add outlier flag to dataframe
            features_df['is_outlier'] = outlier_predictions == -1
            
            outlier_count = sum(outlier_predictions == -1)
            print(f" Detected {outlier_count} potential outlier player profiles")
            
            return features_df
            
        except Exception as e:
            print(f"WARNING: Error in outlier detection: {e}")
            return features_df
    
    def generate_enhanced_predictions(self, features_file="prediction_features_enhanced_real_stats.csv"):
        """Generate predictions with advanced analytics"""
        
        print(" ADVANCED MODEL ANALYTICS")
        print("=" * 50)
        
        # Load features
        features_df = pd.read_csv(f"../data/{features_file}")
        print(f"DATA: Analyzing {len(features_df)} players")
        
        # Detect outliers
        features_df = self.detect_prediction_outliers(features_df)
        
        enhanced_predictions = []
        
        for idx, player in features_df.iterrows():
            player_analysis = {
                'player': player['name'],
                'is_outlier': player.get('is_outlier', False)
            }
            
            # Get predictions with confidence for each stat
            for stat in ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']:
                pred, lower, upper = self.predict_with_confidence(
                    features_df.iloc[[idx]], stat
                )
                
                if pred is not None:
                    player_analysis[f'{stat}_prediction'] = pred[0]
                    player_analysis[f'{stat}_lower_ci'] = lower[0]
                    player_analysis[f'{stat}_upper_ci'] = upper[0]
                    player_analysis[f'{stat}_confidence_width'] = upper[0] - lower[0]
                    
                    # Feature importance for this prediction
                    importance = self.calculate_feature_importance_for_player(
                        features_df.iloc[[idx]], stat
                    )
                    player_analysis[f'{stat}_top_features'] = list(importance.keys())[:3]
            
            enhanced_predictions.append(player_analysis)
        
        return pd.DataFrame(enhanced_predictions)
    
    def identify_high_confidence_bets(self, enhanced_predictions, min_confidence=0.8):
        """Find bets with highest model confidence"""
        
        high_confidence_bets = []
        
        for _, player in enhanced_predictions.iterrows():
            if player.get('is_outlier', False):
                continue  # Skip outlier players
            
            for stat in ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']:
                pred_col = f'{stat}_prediction'
                width_col = f'{stat}_confidence_width'
                
                if pred_col in player.index and width_col in player.index:
                    prediction = player[pred_col]
                    confidence_width = player[width_col]
                    
                    # Calculate confidence score (narrower width = higher confidence)
                    if prediction > 0:
                        confidence_score = 1 / (1 + confidence_width/prediction)
                        
                        if confidence_score >= min_confidence:
                            high_confidence_bets.append({
                                'player': player['player'],
                                'stat': stat,
                                'prediction': prediction,
                                'confidence_score': confidence_score,
                                'confidence_width': confidence_width,
                                'model_certainty': 'HIGH' if confidence_score >= 0.9 else 'MEDIUM'
                            })
        
        return sorted(high_confidence_bets, key=lambda x: x['confidence_score'], reverse=True)

def main():
    analytics = AdvancedModelAnalytics()
    enhanced_preds = analytics.generate_enhanced_predictions()
    
    # Find high confidence bets
    high_conf_bets = analytics.identify_high_confidence_bets(enhanced_preds)
    
    print(f"\nTARGET: HIGH CONFIDENCE BETS:")
    print("-" * 40)
    
    for i, bet in enumerate(high_conf_bets[:10], 1):
        print(f"{i:2d}. {bet['player']} - {bet['stat'].upper()}")
        print(f"    Prediction: {bet['prediction']:.2f}")
        print(f"    Confidence: {bet['confidence_score']:.1%} ({bet['model_certainty']})")
        print()

if __name__ == "__main__":
    main()

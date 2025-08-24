#!/usr/bin/env python3
"""
fix_all_models.py

Comprehensive script to diagnose and fix all model issues:
1. Feature alignment between training and prediction data
2. Pitcher model integration
3. Model validation and retraining
4. Prediction accuracy verification
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ModelFixer:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def diagnose_feature_alignment(self):
        """Check if prediction features match training features"""
        logging.info("🔍 STEP 1: Diagnosing feature alignment...")
        
        # Load training data
        hitter_log = pd.read_csv("../data/hitter_boxscores_full.csv", parse_dates=['date'])
        hitter_feat = pd.read_csv("../data/hitter_rolling_5game_features.csv", parse_dates=['date'])
        
        # Load prediction data
        pred_data = pd.read_csv("../data/fd_hitter_features_final.csv")
        
        logging.info(f"Training features shape: {hitter_feat.shape}")
        logging.info(f"Prediction features shape: {pred_data.shape}")
        
        # Check column overlap
        train_cols = set(hitter_feat.select_dtypes(include=[np.number]).columns)
        pred_cols = set(pred_data.select_dtypes(include=[np.number]).columns)
        
        missing_in_pred = train_cols - pred_cols
        missing_in_train = pred_cols - train_cols
        
        if missing_in_pred:
            self.issues_found.append(f"Missing in prediction data: {list(missing_in_pred)[:10]}...")
            logging.warning(f"❌ Missing {len(missing_in_pred)} features in prediction data")
        
        if missing_in_train:
            self.issues_found.append(f"Missing in training data: {list(missing_in_train)[:10]}...")
            logging.warning(f"❌ Missing {len(missing_in_train)} features in training data")
        
        common_features = train_cols & pred_cols
        logging.info(f"✅ Common features: {len(common_features)}")
        
        return common_features
    
    def fix_pitcher_features(self):
        """Fix pitcher feature loading"""
        logging.info("🔍 STEP 2: Fixing pitcher features...")
        
        pitcher_files = [
            "../data/pitcher_features_probables.csv",
            "../data/fd_pitcher_features_final.csv",
            "../data/pitcher_rolling_5game_features.csv"
        ]
        
        for file_path in pitcher_files:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                logging.info(f"✅ Found pitcher features: {file_path} ({df.shape})")
                self.fixes_applied.append(f"Located pitcher features: {os.path.basename(file_path)}")
                return file_path
            else:
                logging.warning(f"❌ Missing: {file_path}")
        
        self.issues_found.append("No pitcher features file found")
        return None
    
    def validate_model_predictions(self, category, model_path):
        """Validate that model predictions are reasonable"""
        logging.info(f"🔍 STEP 3: Validating {category} model...")
        
        try:
            # Load model
            model = joblib.load(model_path)
            
            # Load appropriate data
            if category in ['strikeouts', 'outs', 'win_binary']:
                # Pitcher model
                log_file = "../data/pitcher_boxscores_full.csv"
                feat_file = "../data/pitcher_rolling_5game_features.csv"
            else:
                # Hitter model
                log_file = "../data/hitter_boxscores_full.csv" 
                feat_file = "../data/hitter_rolling_5game_features.csv"
            
            if not os.path.exists(log_file) or not os.path.exists(feat_file):
                self.issues_found.append(f"Missing data files for {category}")
                return False
            
            log = pd.read_csv(log_file, parse_dates=['date'])
            feat = pd.read_csv(feat_file, parse_dates=['date'])
            
            # Derive target column
            log = self.derive_columns(log, category)
            target_col = self.get_target_column(category)
            
            if target_col not in log.columns:
                self.issues_found.append(f"Missing target column {target_col} for {category}")
                return False
            
            # Merge and prepare data
            df = pd.merge(log, feat, on=['player_id', 'date'], how='inner')
            if len(df) == 0:
                self.issues_found.append(f"No merged data for {category}")
                return False
            
            # Get features
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            feature_cols = [col for col in numeric_cols if col not in ['player_id']]
            
            if hasattr(model, 'feature_names_in_'):
                expected_features = list(model.feature_names_in_)
            else:
                expected_features = feature_cols
            
            # Prepare features
            X = df[feature_cols].copy()
            
            # Add missing features
            for col in expected_features:
                if col not in X.columns:
                    X[col] = 0
            
            # Align columns
            X = X.reindex(columns=expected_features, fill_value=0)
            
            # Make predictions on sample
            sample_size = min(100, len(X))
            X_sample = X.head(sample_size)
            y_actual = df[target_col].head(sample_size)
            
            predictions = model.predict(X_sample)
            
            # Check prediction sanity
            pred_mean = np.mean(predictions)
            pred_std = np.std(predictions)
            actual_mean = np.mean(y_actual)
            actual_std = np.std(y_actual)
            
            logging.info(f"   Predictions - Mean: {pred_mean:.3f}, Std: {pred_std:.3f}")
            logging.info(f"   Actual      - Mean: {actual_mean:.3f}, Std: {actual_std:.3f}")
            
            # Check for issues
            all_same = len(set(np.round(predictions, 3))) == 1
            too_extreme = pred_mean < 0 or pred_mean > actual_mean * 3
            
            if all_same:
                self.issues_found.append(f"{category}: All predictions identical ({pred_mean:.3f})")
                return False
            elif too_extreme:
                self.issues_found.append(f"{category}: Predictions too extreme (mean: {pred_mean:.3f})")
                return False
            else:
                logging.info(f"✅ {category} model predictions look reasonable")
                self.fixes_applied.append(f"{category} model validated")
                return True
                
        except Exception as e:
            self.issues_found.append(f"{category} model validation failed: {str(e)}")
            logging.error(f"❌ {category} validation error: {e}")
            return False
    
    def derive_columns(self, df, category):
        """Derive computed columns"""
        df = df.copy()
        if category == "total_bases":
            df['totalBases'] = (
                df.get('hits', 0) + df.get('doubles', 0) * 2 + 
                df.get('triples', 0) * 3 + df.get('homeRuns', 0) * 4
            )
        elif category == "hrr":
            df['hrr'] = df.get('hits', 0) + df.get('runs', 0) + df.get('rbi', 0)
        elif category == "hr_binary":
            df['homeRuns_binary'] = (df.get('homeRuns', 0) > 0).astype(int)
        elif category == "win_binary":
            df['win_binary'] = (df.get('wins', 0) > 0).astype(int)
        return df
    
    def get_target_column(self, category):
        """Get target column name for category"""
        mapping = {
            "hits": "hits", "total_bases": "totalBases", "runs": "runs", "rbi": "rbi",
            "home_runs": "homeRuns", "hrr": "hrr", "stolen_bases": "stolenBases",
            "hr_binary": "homeRuns_binary", "strikeouts": "strikeOuts", 
            "outs": "outs", "win_binary": "win_binary"
        }
        return mapping.get(category, category)
    
    def retrain_bad_models(self, categories_to_fix):
        """Retrain models that failed validation"""
        logging.info("🔍 STEP 4: Retraining problematic models...")
        
        for category in categories_to_fix:
            logging.info(f"Retraining {category}...")
            
            if category in ['strikeouts', 'outs', 'win_binary']:
                game_log = "../data/pitcher_boxscores_full.csv"
                features = "../data/pitcher_rolling_5game_features.csv"
            else:
                game_log = "../data/hitter_boxscores_full.csv"
                features = "../data/hitter_rolling_5game_features.csv"
            
            cmd = [
                sys.executable, "train_prop_model.py",
                "--category", category,
                "--game-log", game_log,
                "--features", features,
                "--output-dir", f"./models/{category}"
            ]
            
            try:
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logging.info(f"✅ Successfully retrained {category}")
                    self.fixes_applied.append(f"Retrained {category} model")
                else:
                    logging.error(f"❌ Failed to retrain {category}: {result.stderr}")
                    self.issues_found.append(f"Retraining {category} failed")
                    
            except Exception as e:
                logging.error(f"❌ Error retraining {category}: {e}")
                self.issues_found.append(f"Retraining {category} error: {str(e)}")
    
    def create_feature_aligned_prediction_data(self):
        """Create prediction data with proper feature alignment"""
        logging.info("🔍 STEP 5: Creating feature-aligned prediction data...")
        
        try:
            # Load current prediction data
            pred_data = pd.read_csv("../data/fd_hitter_features_final.csv")
            
            # Load training feature template
            feat = pd.read_csv("../data/hitter_rolling_5game_features.csv")
            train_features = feat.select_dtypes(include=[np.number]).columns
            
            # Align prediction data features
            aligned_pred = pred_data.copy()
            
            # Add missing features with appropriate defaults
            for col in train_features:
                if col not in aligned_pred.columns:
                    if 'rate' in col.lower() or 'avg' in col.lower():
                        aligned_pred[col] = 0.250  # Default batting average-like stat
                    elif 'count' in col.lower() or 'games' in col.lower():
                        aligned_pred[col] = 5  # Default count
                    else:
                        aligned_pred[col] = 0  # Default zero
            
            # Save aligned data
            output_file = "../data/fd_hitter_features_aligned.csv"
            aligned_pred.to_csv(output_file, index=False)
            
            logging.info(f"✅ Created feature-aligned prediction data: {output_file}")
            self.fixes_applied.append("Created feature-aligned prediction data")
            
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Error creating aligned data: {e}")
            self.issues_found.append(f"Feature alignment failed: {str(e)}")
            return None
    
    def run_comprehensive_fix(self):
        """Run complete model fixing process"""
        logging.info("🚀 STARTING COMPREHENSIVE MODEL FIX")
        logging.info("=" * 60)
        
        # Step 1: Diagnose feature alignment
        common_features = self.diagnose_feature_alignment()
        
        # Step 2: Fix pitcher features
        pitcher_file = self.fix_pitcher_features()
        
        # Step 3: Validate all models
        categories = [
            "hits", "total_bases", "runs", "rbi", "home_runs", 
            "hrr", "stolen_bases", "hr_binary",
            "strikeouts", "outs", "win_binary"
        ]
        
        bad_models = []
        for category in categories:
            model_paths = [
                f"./models/{category}/{category}_pipeline.joblib",
                f"./models/{category}/{category}_model.pkl"
            ]
            
            model_found = False
            for model_path in model_paths:
                if os.path.exists(model_path):
                    if not self.validate_model_predictions(category, model_path):
                        bad_models.append(category)
                    model_found = True
                    break
            
            if not model_found:
                logging.warning(f"❌ No model found for {category}")
                bad_models.append(category)
        
        # Step 4: Retrain bad models
        if bad_models:
            logging.info(f"Retraining {len(bad_models)} problematic models: {bad_models}")
            self.retrain_bad_models(bad_models)
        
        # Step 5: Create aligned prediction data
        self.create_feature_aligned_prediction_data()
        
        # Summary
        logging.info("\n" + "=" * 60)
        logging.info("🎯 MODEL FIX SUMMARY")
        logging.info("=" * 60)
        
        if self.issues_found:
            logging.info(f"❌ ISSUES FOUND ({len(self.issues_found)}):")
            for issue in self.issues_found:
                logging.info(f"   • {issue}")
        
        if self.fixes_applied:
            logging.info(f"✅ FIXES APPLIED ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                logging.info(f"   • {fix}")
        
        logging.info("\n🚀 Model fixing complete!")
        
        return len(self.issues_found) == 0

def main():
    fixer = ModelFixer()
    success = fixer.run_comprehensive_fix()
    
    if success:
        logging.info("✅ All models fixed successfully!")
        
        # Test the betting system
        logging.info("\n🎯 Testing betting system with fixed models...")
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "automated_betting_system.py",
                "--date", "2025-07-19", "--min-edge", "0.15"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logging.info("✅ Betting system test successful!")
            else:
                logging.error(f"❌ Betting system test failed: {result.stderr}")
                
        except Exception as e:
            logging.error(f"❌ Error testing betting system: {e}")
    else:
        logging.error("❌ Some models still have issues - check the log above")

if __name__ == "__main__":
    main()

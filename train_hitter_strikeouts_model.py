#!/usr/bin/env python3
"""
train_hitter_strikeouts_model.py

Train a dedicated model for hitter strikeouts (batters being struck out) 
using hitter data instead of pitcher data.
"""
import os
import argparse
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_pipeline(task_type="regression"):
    """Build sklearn pipeline with preprocessing"""
    # Identify numeric columns for scaling
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Apply to all numeric columns
    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, make_column_selector(dtype_include=np.number))
    ])
    
    # Add estimator
    if task_type == "regression":
        estimator = GradientBoostingRegressor(random_state=42)
    else:
        raise ValueError("Only regression supported for strikeouts")
    
    return Pipeline([
        ('preprocessor', preprocessor),
        ('estimator', estimator)
    ])

def main():
    parser = argparse.ArgumentParser(description="Train hitter strikeouts model")
    parser.add_argument("--game-log", default="../data/hitter_boxscores_full.csv")
    parser.add_argument("--features", default="../data/hitter_rolling_5game_features.csv") 
    parser.add_argument("--output-dir", default="./models/hitter_strikeouts")
    parser.add_argument("--tune", action='store_true')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    logging.info("Training hitter strikeouts model...")
    
    # Load data
    log = pd.read_csv(args.game_log, parse_dates=['date'])
    feat = pd.read_csv(args.features, parse_dates=['date'])
    
    # Remove duplicate columns from features
    feat = feat.drop(columns=['name', 'strikeOuts'], errors='ignore')
    
    # Target column is strikeOuts (hitters being struck out)
    target_col = 'strikeOuts'
    if target_col not in log.columns:
        logging.error(f"Target column '{target_col}' not found in game log")
        return
    
    # Merge data
    df = log.merge(feat, on=['player_id', 'date'], how='inner', suffixes=('', '_feat'))
    logging.info(f"Merged dataset: {len(df)} rows")
    
    # Prepare features and target
    feature_cols = [col for col in df.columns if col not in [
        'name', 'player_id', 'date', 'team', 'opponent', target_col
    ]]
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Remove rows with missing target
    mask = y.notna()
    X, y = X[mask], y[mask]
    logging.info(f"Final dataset: {len(X)} rows with {len(feature_cols)} features")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=None
    )
    
    # Build pipeline
    pipeline = build_pipeline("regression")
    
    # Hyperparameter tuning if requested
    if args.tune:
        logging.info("Performing hyperparameter tuning...")
        param_dist = {
            'estimator__n_estimators': [100, 200, 300],
            'estimator__max_depth': [3, 5, 7, 10],
            'estimator__learning_rate': [0.01, 0.1, 0.2],
            'estimator__subsample': [0.8, 0.9, 1.0]
        }
        
        search = RandomizedSearchCV(
            pipeline, param_dist, n_iter=20, cv=KFold(n_splits=5, shuffle=True, random_state=42),
            scoring='neg_mean_absolute_error', random_state=42, n_jobs=-1
        )
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        logging.info(f"Best parameters: {search.best_params_}")
    else:
        pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    logging.info(f"Test MAE: {mae:.3f}")
    logging.info(f"Test RMSE: {rmse:.3f}")
    
    # Save model
    model_path = os.path.join(args.output_dir, "hitter_strikeouts_pipeline.joblib")
    joblib.dump(pipeline, model_path)
    logging.info(f"Model saved to {model_path}")
    
    # Save feature names for later use
    feature_names_path = os.path.join(args.output_dir, "feature_names.txt")
    with open(feature_names_path, 'w') as f:
        for name in feature_cols:
            f.write(f"{name}\n")
    
    logging.info("Hitter strikeouts model training complete!")

if __name__ == "__main__":
    main()

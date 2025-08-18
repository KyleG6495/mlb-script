#!/usr/bin/env python3
"""
Quick Enhanced Model Trainer for MLB Predictions
Creates models that work with our current data structure
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder
import pickle
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_models():
    """Create enhanced ML models for predictions"""
    logger.info("START: QUICK ENHANCED MODEL TRAINER")
    logger.info("=" * 50)
    
    # Load training data
    logger.info("DATA: Loading training data...")
    try:
        df = pd.read_csv("../data/prediction_features_enhanced_real_stats.csv")
        logger.info(f"SUCCESS: Loaded {len(df)} training samples")
    except FileNotFoundError:
        logger.error("ERROR: Training data not found!")
        return
    
    # Prepare features
    exclude_cols = ['Id', 'First Name', 'Last Name', 'name', 'player_id', 'date']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Handle categorical columns
    categorical_cols = ['Team', 'Opponent', 'team', 'opponent']
    numerical_cols = [col for col in feature_cols if col not in categorical_cols]
    
    # Encode categorical variables
    le_dict = {}
    df_encoded = df.copy()
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df[col].astype(str))
            le_dict[col] = le
    
    # Define target variables
    targets = {
        'hits': 'hits',
        'homeRuns': 'homeRuns', 
        'runs': 'runs',
        'rbi': 'rbi',
        'stolenBases': 'stolenBases'
    }
    
    # Create models directory
    os.makedirs("../models", exist_ok=True)
    
    # Train models for each target
    for model_name, target_col in targets.items():
        if target_col not in df.columns:
            logger.warning(f"WARNING: Target {target_col} not found, skipping...")
            continue
            
        logger.info(f"TARGET: Training {model_name} model...")
        
        # Prepare data
        X = df_encoded[feature_cols]
        y = df_encoded[target_col]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Create preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_cols),
                ('cat', 'passthrough', categorical_cols)
            ],
            remainder='passthrough'
        )
        
        # Create and train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        # Fit preprocessor and model
        X_train_processed = preprocessor.fit_transform(X_train)
        model.fit(X_train_processed, y_train)
        
        # Test the model
        X_test_processed = preprocessor.transform(X_test)
        score = model.score(X_test_processed, y_test)
        
        logger.info(f"   DATA: {model_name} R score: {score:.3f}")
        
        # Save model and preprocessor together
        model_data = {
            'model': model,
            'preprocessor': preprocessor,
            'features': feature_cols,
            'categorical_encoders': le_dict,
            'score': score
        }
        
        model_path = f"../models/{model_name}_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
            
        logger.info(f"   SUCCESS: Saved {model_name} model to {model_path}")
    
    logger.info("COMPLETE: Model training complete!")

if __name__ == "__main__":
    create_models()

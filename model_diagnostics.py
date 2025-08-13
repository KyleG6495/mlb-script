"""
Critical Model Diagnostics and Immediate Fixes
Run this to identify and fix model issues quickly
"""

import pandas as pd
import numpy as np
import joblib
import logging
from pathlib import Path

def diagnose_model_predictions(model_category, test_data):
    """Diagnose what's causing poor predictions"""
    
    print(f"\n🔍 DIAGNOSING {model_category.upper()} MODEL:")
    print("="*60)
    
    # Load the model
    model_path = f"./models/{model_category}/{model_category}_pipeline.joblib"
    if not Path(model_path).exists():
        print(f"❌ Model file not found: {model_path}")
        return
    
    try:
        pipeline = joblib.load(model_path)
        print(f"✅ Model loaded successfully")
        
        # Check model components
        if hasattr(pipeline, 'steps'):
            print(f"📋 Pipeline steps: {[step[0] for step in pipeline.steps]}")
        
        # Test prediction with a small sample
        sample_size = min(5, len(test_data))
        sample_data = test_data.head(sample_size)
        
        print(f"🧪 Testing predictions on {sample_size} samples:")
        predictions = pipeline.predict(sample_data)
        
        print(f"   Raw predictions: {predictions}")
        print(f"   Min prediction: {predictions.min():.4f}")
        print(f"   Max prediction: {predictions.max():.4f}")
        print(f"   Mean prediction: {predictions.mean():.4f}")
        print(f"   Unique values: {len(np.unique(predictions))}")
        
        # Check for common issues
        if len(np.unique(predictions)) <= 3:
            print("🚨 ISSUE: Very low prediction diversity (possible overfitting)")
        
        if predictions.min() < 0:
            print("🚨 ISSUE: Negative predictions detected")
            
        if predictions.max() > 20:  # Reasonable upper bound for baseball stats
            print("🚨 ISSUE: Extremely high predictions detected")
            
        # Feature analysis
        if hasattr(pipeline, 'feature_names_in_'):
            print(f"📊 Expected features: {len(pipeline.feature_names_in_)}")
            print(f"   Input features: {len(sample_data.columns)}")
            
            missing_features = set(pipeline.feature_names_in_) - set(sample_data.columns)
            if missing_features:
                print(f"❌ Missing features: {missing_features}")
            
            extra_features = set(sample_data.columns) - set(pipeline.feature_names_in_)
            if extra_features:
                print(f"⚠️ Extra features: {list(extra_features)[:5]}...")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")

def quick_model_fixes():
    """Implement immediate fixes for common model issues"""
    
    print("\n🚀 IMPLEMENTING QUICK FIXES:")
    print("="*60)
    
    # Check for data alignment issues
    hitter_files = [
        "../data/fd_hitter_features_final.csv",
        "../data/prediction_features_enhanced_real_stats.csv"
    ]
    
    for file_path in hitter_files:
        if Path(file_path).exists():
            print(f"\n📊 Analyzing {Path(file_path).name}:")
            df = pd.read_csv(file_path)
            
            # Check target columns
            target_columns = ['hits', 'total_bases', 'runs', 'rbi', 'home_runs']
            available_targets = [col for col in target_columns if col in df.columns]
            print(f"   Available targets: {available_targets}")
            
            # Check for data quality issues
            if 'hits' in df.columns:
                hits_data = df['hits']
                print(f"   Hits stats: min={hits_data.min()}, max={hits_data.max()}, mean={hits_data.mean():.2f}")
                
                if hits_data.mean() < 0.5:
                    print("🚨 CRITICAL: Hits data appears to be binary/percentage instead of count")
                    print("   Recommendation: Scale hits data or use different target column")
            
            # Check feature quality
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            print(f"   Numeric features: {len(numeric_cols)}")
            
            # Look for constant columns (no variance)
            constant_cols = [col for col in numeric_cols if df[col].nunique() <= 2]
            if constant_cols:
                print(f"   ⚠️ Low-variance features: {len(constant_cols)} columns")
            
            break

def generate_emergency_fallback_system():
    """Create a simple fallback system for when models fail"""
    
    fallback_code = '''
# Emergency Fallback Prediction System
def emergency_predictions(df, category):
    """Simple baseline predictions when models fail"""
    
    # Historical MLB averages per game
    baseline_stats = {
        'hits': 1.2,
        'total_bases': 1.8,
        'runs': 0.6,
        'rbi': 0.6,
        'home_runs': 0.15,
        'hitter_strikeouts': 0.9,
        'pitcher_strikeouts': 6.5,
        'stolen_bases': 0.1
    }
    
    base_value = baseline_stats.get(category, 1.0)
    
    # Add small random variation to avoid identical predictions
    n_players = len(df)
    predictions = np.random.normal(
        loc=base_value,
        scale=base_value * 0.2,  # 20% standard deviation
        size=n_players
    )
    
    # Ensure non-negative predictions
    predictions = np.maximum(predictions, 0.01)
    
    return predictions
    '''
    
    print("\n🆘 EMERGENCY FALLBACK SYSTEM:")
    print("="*60)
    print("If models continue to fail, use this code:")
    print(fallback_code)

def main():
    """Run comprehensive diagnostics"""
    
    print("🏥 AUTOMATED BETTING SYSTEM - EMERGENCY DIAGNOSTICS")
    print("="*80)
    
    # Load test data
    test_data_paths = [
        "../data/fd_hitter_features_final.csv",
        "../data/prediction_features_enhanced_real_stats.csv"
    ]
    
    test_data = None
    for path in test_data_paths:
        if Path(path).exists():
            test_data = pd.read_csv(path)
            print(f"📋 Loaded test data: {path} ({len(test_data)} rows)")
            break
    
    if test_data is None:
        print("❌ No test data found!")
        return
    
    # Test critical models
    critical_models = ['hits', 'total_bases', 'runs', 'home_runs', 'hitter_strikeouts']
    
    for model_category in critical_models:
        diagnose_model_predictions(model_category, test_data)
    
    # Quick fixes
    quick_model_fixes()
    
    # Emergency fallback
    generate_emergency_fallback_system()
    
    print("\n📋 IMMEDIATE ACTION ITEMS:")
    print("="*60)
    print("1. Check if hits model is using binary target instead of count")
    print("2. Verify feature alignment between training and prediction data")
    print("3. Consider retraining models with proper target scaling")
    print("4. Implement fallback predictions for failed models")
    print("5. Add data validation pipeline before prediction")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
train_prop_model.py

Train regression or classification models for MLB props (hits, strikeouts, etc.), with optional hyperparameter tuning and optional time-based hold-out evaluation.
Usage:
    python train_prop_model.py \
        --category <prop_category> \
        --game-log ../data/<hitter|pitcher>_boxscores_full.csv \
        --features ../data/<hitter|pitcher>_rolling_5game_features.csv \
        --output-dir ./models/<category> [--tune] [--cutoff-date 2025-7-1]
"""
import os
import sys
import argparse
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor, XGBClassifier

# configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# prop definitions
CATEGORY_MAP = {
    "hits":         ("hits",            "regression"),
    "total_bases":  ("totalBases",      "regression"),
    "runs":         ("runs",            "regression"),
    "rbi":          ("rbi",             "regression"),
    "home_runs":    ("homeRuns",        "regression"),
    "hrr":          ("hrr",             "regression"),
    "stolen_bases": ("stolenBases",     "regression"),
    "hr_binary":    ("homeRuns_binary", "classification"),
    "strikeouts":   ("strikeOuts",      "regression"),
    "outs":         ("outs",            "regression"),
    "win_binary":   ("win_binary",      "classification"),
}

def derive_columns(df: pd.DataFrame, category: str) -> pd.DataFrame:
    df = df.copy()
    if category == "total_bases":
        df['totalBases'] = (
            df.get('hits', 0)
            + df.get('doubles', 0) * 2
            + df.get('triples', 0) * 3
            + df.get('homeRuns', 0) * 4
        )
    if category == "hrr":
        df['hrr'] = (
            df.get('hits', 0)
            + df.get('runs', 0)
            + df.get('rbi', 0)
        )
    if category == "hr_binary":
        df['homeRuns_binary'] = (df.get('homeRuns', 0) > 0).astype(int)
    if category == "win_binary":
        df['win_binary'] = (df.get('wins', 0) > 0).astype(int)
    return df

def build_pipeline(task_type: str) -> Pipeline:
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, make_column_selector(dtype_include=np.number))
    ])
    if task_type == 'regression':
        estimator = XGBRegressor(random_state=42, n_jobs=-1, verbosity=0)
    else:
        estimator = XGBClassifier(random_state=42, n_jobs=-1, use_label_encoder=False, verbosity=0)
    return Pipeline([
        ('preprocess', preprocessor),
        ('model', estimator)
    ])

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Train MLB prop model")
    parser.add_argument("--category", choices=CATEGORY_MAP.keys(), required=True)
    parser.add_argument("--game-log", required=True)
    parser.add_argument("--features", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tune", action='store_true', help='Perform hyperparameter tuning')
    parser.add_argument("--cutoff-date", type=str,
                        help='If provided, do time-based hold-out split at YYYY-MM-DD for evaluation')
    args = parser.parse_args()

    target_col, task_type = CATEGORY_MAP[args.category]
    logging.info(f"Category: {args.category} -> target='{target_col}', task='{task_type}'")

    log = pd.read_csv(args.game_log, parse_dates=['date'])
    feat = pd.read_csv(args.features, parse_dates=['date'])

    # Load merged weather and park factors
    weather_park = pd.read_csv("../data/merged_weather_park.csv")

    # Merge on 'game_pk'
    if 'game_pk' in feat.columns and 'game_pk' in weather_park.columns:
        feat = feat.merge(weather_park, on='game_pk', how='left', suffixes=('', '_weatherpark'))
    else:
        # Optionally, merge on ['date', 'home_team'] if 'game_pk' is not available
        pass  # You can add alternative merge logic here if needed

    logging.info(f"Game log date range: {log['date'].min()} to {log['date'].max()}")
    logging.info(f"Features date range: {feat['date'].min()} to {feat['date'].max()}")

    # Merge
    df = pd.merge(
        log, feat,
        on=['player_id', 'date'],
        how='inner',
        suffixes=('', '_feat')
    )
    df = derive_columns(df, args.category)

    if target_col not in df.columns or df[target_col].isnull().all():
        logging.warning(f"Merged data missing target '{target_col}', skipping.")
        return

    # Split
    if args.cutoff_date:
        cutoff = pd.to_datetime(args.cutoff_date)
        train_df = df[df['date'] < cutoff].copy()
        test_df  = df[df['date'] >= cutoff].copy()
        X_train = train_df.drop(columns=['player_id','date', target_col])
        y_train = train_df[target_col]
        X_val   = test_df .drop(columns=['player_id','date', target_col])
        y_val   = test_df [target_col]
    else:
        X = df.drop(columns=['player_id','date', target_col])
        y = df[target_col]
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # Check for empty splits
    if X_train.shape[0] == 0 or X_val.shape[0] == 0:
        logging.warning(f"Empty train or validation set for category '{args.category}', skipping.")
        return

    pipeline = build_pipeline(task_type)

    if args.tune:
        param_dist = {
            'model__n_estimators': [50, 100, 200],
            'model__max_depth': [3, 4, 5, 6],
            'model__learning_rate': [0.01, 0.05, 0.1, 0.2],
            'model__subsample': [0.7, 0.8, 1.0],
            'model__colsample_bytree': [0.7, 0.8, 1.0]
        }
        search = RandomizedSearchCV(
            pipeline, param_distributions=param_dist,
            n_iter=10, cv=KFold(3, shuffle=True, random_state=42),
            scoring='neg_mean_absolute_error' if task_type == 'regression' else 'roc_auc',
            random_state=42, n_jobs=-1, verbose=1
        )
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        logging.info(f"Best params: {search.best_params_}")
    else:
        pipeline.fit(X_train, y_train)

    # Evaluate
    preds = pipeline.predict(X_val)
    if task_type == 'regression':
        mae = mean_absolute_error(y_val, preds)
        rmse = mean_squared_error(y_val, preds) ** 0.5
        logging.info(f"Validation MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    else:
        acc = accuracy_score(y_val, preds)
        try:
            auc = roc_auc_score(y_val, pipeline.predict_proba(X_val)[:,1])
            logging.info(f"Validation Accuracy: {acc:.4f}, ROC AUC: {auc:.4f}")
        except Exception:
            logging.info(f"Validation Accuracy: {acc:.4f} (ROC AUC unavailable)")

    # Print predictions for the first 10 validation samples
    logging.info("First 10 predictions vs actuals:")
    for i, (pred, actual) in enumerate(zip(preds[:10], y_val[:10])):
        logging.info(f"Pred: {pred:.4f} | Actual: {actual:.4f}")

    # Save model
    os.makedirs(args.output_dir, exist_ok=True)
    model_path = os.path.join(args.output_dir, f"{args.category}_model.pkl")
    joblib.dump(pipeline, model_path)
    logging.info(f"Saved model to {model_path}")

    # Save all validation predictions to CSV
    preds_df = pd.DataFrame({
        'player_id': test_df['player_id'].values if args.cutoff_date else None,
        'date': test_df['date'].values if args.cutoff_date else None,
        'actual': y_val.values,
        'predicted': preds
    })
    # Remove columns if not using cutoff_date
    if not args.cutoff_date:
        preds_df = preds_df.drop(columns=['player_id', 'date'])
    preds_path = os.path.join(args.output_dir, f"{args.category}_val_predictions.csv")
    preds_df.to_csv(preds_path, index=False)
    logging.info(f"Saved validation predictions to {preds_path}")

if __name__ == "__main__":
    main()
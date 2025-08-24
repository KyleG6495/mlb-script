#!/usr/bin/env python3
"""
train_prop_model.py

Train regression or classification models for MLB props (hits, strikeouts, etc.), with optional hyperparameter tuning.
Usage:
    python train_prop_model.py \
        --category <prop_category> \
        --game-log ../data/<hitter|pitcher>_boxscores_full.csv \
        --features ../data/<hitter|pitcher>_rolling_5game_features.csv \
        --output-dir ./models/<category> [--tune]
"""
import os
import argparse
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

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
        estimator = GradientBoostingRegressor(random_state=42)
    else:
        estimator = GradientBoostingClassifier(random_state=42)
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
    args = parser.parse_args()

    target_col, task_type = CATEGORY_MAP[args.category]
    logging.info(f"Category: {args.category} -> target='{target_col}', task='{task_type}'")

    # load data
    log = pd.read_csv(args.game_log, parse_dates=['date'])
    feat = pd.read_csv(args.features, parse_dates=['date'])

    # drop duplicate name and target from features to avoid collisions
    feat = feat.drop(columns=['name', target_col], errors='ignore')

    # derive computed columns
    log = derive_columns(log, args.category)
    if target_col not in log.columns:
        logging.warning(f"Target column '{target_col}' missing for category '{args.category}', skipping.")
        return

    # merge datasets including player name
    df = pd.merge(
        log[['player_id', 'name', 'date', target_col]],
        feat,
        on=['player_id', 'date'], how='inner'
    )
    if target_col not in df.columns:
        logging.warning(f"Merged data missing target '{target_col}', skipping.")
        return
    df = df.dropna(subset=[target_col])

    # prepare features and labels
    X = df.drop(columns=['player_id', 'name', 'date', target_col])
    y = df[target_col].astype(float if task_type=='regression' else int)
    if task_type=='classification' and len(np.unique(y))<2:
        logging.warning(f"Only one class present for '{args.category}', skipping.")
        return

    # train/validation split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = build_pipeline(task_type)
    if args.tune:
        param_dist = {
            'model__n_estimators': [100,200,300],
            'model__learning_rate': [0.01,0.1,0.2],
            'model__max_depth': [3,5,7]
        }
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        scoring = 'neg_mean_absolute_error' if task_type=='regression' else 'roc_auc'
        search = RandomizedSearchCV(pipeline, param_distributions=param_dist,
                                   n_iter=10, cv=cv, scoring=scoring,
                                   random_state=42, n_jobs=-1)
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        logging.info(f"Best params: {search.best_params_}")
    else:
        pipeline.fit(X_train, y_train)

    # evaluate and save predictions
    preds = pipeline.predict(X_val)
    results = df.loc[X_val.index, ['player_id', 'name', 'date']].copy()
    results['actual'] = y_val.values
    results['predicted'] = preds

    os.makedirs(args.output_dir, exist_ok=True)
    out_csv = os.path.join(args.output_dir, f"predictions_{args.category}.csv")
    results.to_csv(out_csv, index=False)
    logging.info(f"Validation predictions saved to: {out_csv}")

    # save model pipeline
    model_path = os.path.join(args.output_dir, f"{args.category}_pipeline.joblib")
    joblib.dump(pipeline, model_path)
    logging.info(f"Model pipeline saved to: {model_path}")

if __name__ == '__main__':
    main()

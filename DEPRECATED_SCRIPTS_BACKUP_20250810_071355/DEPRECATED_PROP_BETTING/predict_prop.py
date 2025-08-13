#!/usr/bin/env python3
"""
predict_prop.py

Load a trained strikeouts model and compute P(K ≥ line) for today’s probables,
automatically aligning any missing or extra features.
"""
import argparse
import pandas as pd
import numpy as np
import joblib
from scipy import stats

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",    required=True,
                        help="Path to your trained model (.joblib)")
    parser.add_argument("--features", required=True,
                        help="CSV of today’s probables with feature columns")
    parser.add_argument("--lines",    nargs="+", type=float, required=True,
                        help="Prop lines to compute P(over) for (e.g. 5.5 6.5 7.5)")
    parser.add_argument("--output",   required=True,
                        help="Where to save the predictions CSV")
    parser.add_argument("--sigma",    type=float, default=1.24,
                        help="Error σ (use your validation RMSE)")
    args = parser.parse_args()

    # Load model and grab exact feature names
    model = joblib.load(args.model)
    expected = list(model.feature_names_in_)

    # Load your probables table
    df = pd.read_csv(args.features)

    # If last‐game K’s column exists, rename it to match training
    if "strikeOuts" in df.columns and "strikeOuts_feat" in expected:
        df = df.rename(columns={"strikeOuts": "strikeOuts_feat"})

    # Build X from all numeric columns
    X = df.select_dtypes(include=[np.number]).copy()

    # Add any missing features (fill with zero)
    for col in expected:
        if col not in X.columns:
            X[col] = 0

    # Drop any extras and ensure column order matches training
    X = X[expected]

    # Predict point‐estimate
    df["predicted_K"] = model.predict(X)

    # Compute P(K ≥ line) for each requested line
    for line in args.lines:
        df[f"P(K ≥ {line})"] = 1 - stats.norm.cdf(
            line, loc=df["predicted_K"], scale=args.sigma
        )

    # Save results
    df.to_csv(args.output, index=False)
    print(f"✅ Saved predictions to {args.output}")

if __name__ == "__main__":
    main()

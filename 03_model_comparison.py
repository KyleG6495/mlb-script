# 03_model_comparison.py

import pandas as pd
import numpy as np
from math import sqrt
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

# 1. Load data
df = pd.read_csv("../data/hitter_features_with_schedule.csv")
df["log_Salary"] = np.log(df["Salary"])

# Drop rows missing our primary fields
df = df.dropna(subset=["FPPG", "log_Salary", "Played", "Position", "Team", "Opponent", "venue"])

# 2. Define features
numeric_features = ["log_Salary", "Played"]
categorical_features = ["Position", "Team", "Opponent", "venue"]

# 3. Preprocessing pipeline
preprocessor = ColumnTransformer(transformers=[
    ("num", StandardScaler(), numeric_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
])

# 4. Models to compare
models = {
    "LinearRegression": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "Lasso": Lasso(alpha=0.1),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
}

# 5. Run cross‐validation
results = {}
for name, estimator in models.items():
    pipe = Pipeline(steps=[
        ("pre", preprocessor),
        ("model", estimator)
    ])
    # Using negative MSE, so we take sqrt of the absolute
    neg_mse = cross_val_score(pipe, df, df["FPPG"],
                              cv=5,
                              scoring="neg_mean_squared_error",
                              n_jobs=-1)
    rmse_scores = np.sqrt(-neg_mse)
    results[name] = rmse_scores.mean()
    print(f"{name} CV RMSE: {rmse_scores.mean():.4f}")

# 6. Print summary
print("\nMean CV RMSE by model:")
for name, rmse in results.items():
    print(f"  {name:<20} {rmse:.4f}")

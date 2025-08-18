import pandas as pd
import numpy as np
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt
import joblib
import json

print("SWAP: Loading enhanced hitter features...")

# 1. Load your NEW enhanced dataset
df = pd.read_csv("../data/hitters_enhanced_features.csv")
print(f"DATA: Loaded enhanced dataset: {df.shape}")

# Quick check of your enhanced data
print(f"Dataset shape: {df.shape}")
print(f"FPPG non-null: {df['FPPG'].notna().sum()}")
print(f"Season stats availability:")
for col in ['atBats_season', 'hits_season', 'homeRuns_season']:
    if col in df.columns:
        print(f"  {col}: {df[col].notna().sum()} non-null")

# 2. Remove rows with missing target variable
df = df.dropna(subset=["FPPG"])
print(f"DATA: After removing missing FPPG: {df.shape}")

# 3. Select the BEST features based on your correlation analysis
top_features = [
    'Salary', 'Played', 'atBats_season', 'rbi_season', 'hits_season',
    'doubles_season', 'baseOnBalls_season', 'season_avg', 'strikeOuts_season',
    'homeRuns_season', 'season_rbi_rate', 'season_hr_rate'
]

# Only use features that exist and have sufficient data
available_features = []
for feature in top_features:
    if feature in df.columns:
        non_null_count = df[feature].notna().sum()
        if non_null_count >= 100:  # Need at least 100 data points
            available_features.append(feature)
            print(f"SUCCESS: {feature}: {non_null_count} non-null values")
        else:
            print(f"ERROR: {feature}: Only {non_null_count} non-null values")

print(f"\nTARGET: Using {len(available_features)} features: {available_features}")

# 4. Prepare final dataset
df_model = df[available_features + ['FPPG']].dropna()
print(f"DATA: Final modeling dataset: {df_model.shape}")

X = df_model[available_features]
y = df_model['FPPG']

# 5. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\nDATA: Training set: {X_train.shape}")
print(f"DATA: Test set: {X_test.shape}")

# 3. Fit linear regression
model = LinearRegression()
model.fit(X_train, y_train)

# 4. Predict & evaluate
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = sqrt(mse)

print("Linear Regression baseline")
print(f"  Coefficients: {dict(zip(X.columns, model.coef_))}")
print(f"  Intercept: {model.intercept_:.4f}")
print(f"  Test R: {r2:.4f}")
print(f"  Test RMSE: {rmse:.4f}")

#%%
# Compute residuals
residuals = y_test - y_pred

plt.figure()
plt.scatter(y_pred, residuals, alpha=0.5)
plt.axhline(0, color="black", linestyle="--")
plt.xlabel("Predicted FPPG")
plt.ylabel("Residual (Actual  Predicted)")
plt.title("Residuals vs. Predicted FPPG")
plt.savefig("../data/residuals_vs_predicted.png")
print("Saved residual plot to ../data/residuals_vs_predicted.png")

#%%
# Build a small DataFrame of predictions and absolute residuals
df_res = pd.DataFrame({
    "pred": y_pred,
    "abs_resid": np.abs(residuals)
})

# 1) Correlation between predicted value and abs(residual)
corr = df_res["pred"].corr(df_res["abs_resid"])
print(f"Correlation between predicted FPPG and |residual|: {corr:.4f}")

# 2) Std dev of abs residuals in prediction bins
df_res["pred_bin"] = pd.qcut(df_res["pred"], 5)  # 5 equal-frequency bins
std_by_bin = df_res.groupby("pred_bin")["abs_resid"].std()
print("\nResidual std dev by predicted-FPPG quintile:")
print(std_by_bin.to_string())

print("\nSWAP: Testing Advanced Models...")

# Random Forest
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_r2 = r2_score(y_test, rf_pred)
rf_rmse = sqrt(mean_squared_error(y_test, rf_pred))

print(f"\n Random Forest:")
print(f"  Test R: {rf_r2:.4f}")
print(f"  Test RMSE: {rf_rmse:.4f}")

# Ridge Regression  
ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)
ridge_pred = ridge.predict(X_test)
ridge_r2 = r2_score(y_test, ridge_pred)
ridge_rmse = sqrt(mean_squared_error(y_test, ridge_pred))

print(f"\n Ridge Regression:")
print(f"  Test R: {ridge_r2:.4f}")
print(f"  Test RMSE: {ridge_rmse:.4f}")

# Feature Importance (Random Forest)
feature_importance = pd.DataFrame({
    'feature': available_features,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nTARGET: Feature Importance (Random Forest):")
print(feature_importance.to_string(index=False))

# Best model for fantasy predictions
final_model = RandomForestRegressor(n_estimators=100, random_state=42)
final_model.fit(X_train, y_train)

print("\n Saving models...")

# Save the Random Forest model
joblib.dump(rf, '../data/random_forest_model.pkl')
print("SUCCESS: Saved Random Forest model to ../data/random_forest_model.pkl")

# Save model configuration
feature_config = {
    'features': available_features,
    'model_performance': {
        'r2': rf_r2,
        'rmse': rf_rmse,
        'training_samples': len(X_train),
        'test_samples': len(X_test)
    }
}

with open('../data/model_config.json', 'w') as f:
    json.dump(feature_config, f, indent=2)
print("SUCCESS: Saved model configuration to ../data/model_config.json")

print(f"\nLINEUP: MODEL SAVED - Ready for lineup optimization!")
print(f"DATA: Performance: R = {rf_r2:.4f}, RMSE = {rf_rmse:.4f}")



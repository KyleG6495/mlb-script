import pandas as pd
import numpy as np
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# 1. Load and prepare data
df = pd.read_csv("../data/hitter_features_with_schedule.csv")
df["log_Salary"] = np.log(df["Salary"])
df = df.dropna(subset=["FPPG", "log_Salary", "Played"])

# Features and target
X = df[["log_Salary", "Played"]]
y = df["FPPG"]

# 2. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

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
print(f"  Test R²: {r2:.4f}")
print(f"  Test RMSE: {rmse:.4f}")

#%%
import matplotlib.pyplot as plt

# Compute residuals
residuals = y_test - y_pred

plt.figure()
plt.scatter(y_pred, residuals, alpha=0.5)
plt.axhline(0, color="black", linestyle="--")
plt.xlabel("Predicted FPPG")
plt.ylabel("Residual (Actual − Predicted)")
plt.title("Residuals vs. Predicted FPPG")
plt.savefig("../data/residuals_vs_predicted.png")
print("Saved residual plot to ../data/residuals_vs_predicted.png")

#%%
import pandas as pd
import numpy as np

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



import pandas as pd
import numpy as np
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 1. Load & prep
df = pd.read_csv("../data/hitter_features_with_schedule.csv")
df["log_Salary"] = np.log(df["Salary"])
df = df.dropna(subset=["FPPG", "log_Salary", "Played"])

X = df[["log_Salary", "Played"]]
y = df["FPPG"]

# 2. Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. Fit GB
gb = HistGradientBoostingRegressor(random_state=42)
gb.fit(X_train, y_train)

# 4. Evaluate
y_pred = gb.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = sqrt(mean_squared_error(y_test, y_pred))

print("HistGradientBoostingRegressor")
print(f"  Test R²:   {r2:.4f}")
print(f"  Test RMSE: {rmse:.4f}")

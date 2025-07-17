import pandas as pd
import numpy as np
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 1. Load & prep
df = pd.read_csv("../data/hitter_features_with_schedule.csv")
df["log_Salary"] = np.log(df["Salary"])
df = df.dropna(subset=[
    "FPPG", "log_Salary", "Played",
    "Position", "Team", "Opponent", "venue"
])

# 2. Features / target
numeric_features = ["log_Salary", "Played"]
categorical_features = ["Position", "Team", "Opponent", "venue"]
X = df[numeric_features + categorical_features]
y = df["FPPG"]

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Preprocessing
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numeric_features),
    # Use sparse_output=False so the transformer emits a dense array:
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
])

# 5. Pipeline with GB regressor
pipeline = Pipeline([
    ("prep", preprocessor),
    ("gb", HistGradientBoostingRegressor(random_state=42))
])

# 6. Fit & evaluate
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = sqrt(mean_squared_error(y_test, y_pred))

print("Full-feature Gradient Boosting")
print(f"  Test R²:   {r2:.4f}")
print(f"  Test RMSE: {rmse:.4f}")

import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split

# 1. Load & prepare data
df = pd.read_csv("../data/hitter_features_with_schedule.csv")
df["log_Salary"] = np.log(df["Salary"])
df = df.dropna(subset=[
    "FPPG", "log_Salary", "Played",
    "Position", "Team", "Opponent", "venue"
])

# 2. Features + target
X = df[["log_Salary", "Played", "Position", "Team", "Opponent", "venue"]]
y = df["FPPG"]

# 3. Preprocessor (same as before)
numeric_features = ["log_Salary", "Played"]
categorical_features = ["Position", "Team", "Opponent", "venue"]
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numeric_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
])

# 4. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 5. LassoCV pipeline
pipeline = Pipeline([
    ("pre", preprocessor),
    ("lassocv", LassoCV(
        alphas=np.logspace(-3, 1, 50),
        cv=5,
        max_iter=5000,
        random_state=42
    ))
])

# 6. Fit & report
pipeline.fit(X_train, y_train)
best_alpha = pipeline.named_steps["lassocv"].alpha_
print(f"Best alpha found: {best_alpha:.5f}")

# 7. Evaluate on test set
from sklearn.metrics import mean_squared_error, r2_score
from math import sqrt

y_pred = pipeline.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = sqrt(mean_squared_error(y_test, y_pred))
print(f"Test R²:   {r2:.4f}")
print(f"Test RMSE: {rmse:.4f}")

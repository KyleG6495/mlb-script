import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

# Load data
df = pd.read_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/finalize_hitter_features.csv')
print("Columns in df before dropna:", df.columns.tolist())
df = df.dropna()

# Ensure player_id is string
df['player_id'] = df['player_id'].astype(str)

# Merge with fd_hitter_features_final.csv
fd_df = pd.read_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/fd_hitter_features_final.csv')
fd_df['player_id'] = fd_df['player_id'].astype(str)  # Ensure string type
df = df.merge(fd_df[['player_id', 'Id', 'Position', 'Team']], on='player_id', how='left')
print("Columns in df after merge:", df.columns.tolist())

# Filter out low-plate-appearance players (Played == 0)
df = df[df['Played'] > 0]
print(f"Rows after filtering low-plate-appearance players: {len(df)}")

# Features and target
features = ['FPPG', 'log_Salary', 'rolling_avg_hits', 'rolling_avg_OBP', 'park_factor', 'temperature']
X = df[features]
y = df['FPPG']  # Use FPPG as target (fantasy points)

# Transform target to handle skewness
y = np.log1p(y)  # Log transform

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train model
model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_pred = np.expm1(y_pred)  # Inverse log transform
y_test = np.expm1(y_test)
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("Full-feature GB model:")
print(f"  Test R²:   {r2:.4f}")
print(f"  Test RMSE: {rmse:.4f}")
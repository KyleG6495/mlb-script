import pandas as pd

# Load your data
hitters = pd.read_csv("../data/hitter_features_with_schedule.csv")
pitchers = pd.read_csv("../data/pitcher_features_with_schedule.csv")

print("BEFORE DROP:")
print(" Hitters shape:", hitters.shape)
print(" Pitchers shape:", pitchers.shape)

# --- Drop fully-empty columns in hitters ---
hitters = hitters.dropna(axis=1, how="all")

# --- Drop 100% empty and >80% empty columns in pitchers ---
# Always drop these two
pitchers = pitchers.drop(columns=["Batting Order", "Tier"], errors="ignore")
# Then drop any column with >80% missing
cols_to_drop = pitchers.columns[pitchers.isna().mean() > 0.8]
pitchers = pitchers.drop(columns=cols_to_drop, errors="ignore")

print("\nAFTER DROP:")
print(" Hitters shape:", hitters.shape)
print(" Pitchers shape:", pitchers.shape)

import numpy as np

# --- Identify high correlations (>0.9) among numeric features ---

def report_high_corr(df, name):
    nums = df.select_dtypes(include="number")
    corr = nums.corr().abs()
    # Only look at the upper triangle, excluding the diagonal
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    # Stack into pairs and filter
    high_pairs = upper.stack().sort_values(ascending=False)
    print(f"\nHigh correlations in {name} (>0.90):")
    if high_pairs.empty:
        print(" None found.")
    else:
        print(high_pairs[high_pairs > 0.90].to_string())

report_high_corr(hitters, "Hitters")
report_high_corr(pitchers, "Pitchers")

#%%
# --- Prune highly correlated features for modeling ---

# Drop atBats (collinear with outs)
pitchers = pitchers.drop(columns=["atBats"], errors="ignore")

# Separate salary from training features
salary_series = pitchers.pop("Salary")  # removes it from pitchers, but keeps it if needed later

print("\nAfter dropping atBats and separating Salary:")
print(" Pitchers features:", pitchers.shape)
print(" Salary series:", salary_series.shape)

#%%
# Step 6a: list hitters columns and show first 5 rows
print("\n--- Hitters columns: ---")
print(hitters.columns.tolist())
print("\n--- First 5 hitters rows: ---")
print(hitters.head())

#%%
# Step 6b: correlation of numeric features with FPPG
# Select only numeric columns
numeric_cols = hitters.select_dtypes(include="number")

# Compute absolute correlations with the target, FPPG
corr_target = numeric_cols.corr()["FPPG"].abs().sort_values(ascending=False)

print("\n=== Correlation with FPPG (descending) ===")
print(corr_target.to_string())

#%%
import matplotlib.pyplot as plt

# Plot the distribution of Salary
plt.figure()
hitters["Salary"].hist(bins=30)
plt.title("Distribution of Hitters' Salary")
plt.xlabel("Salary")
plt.ylabel("Count")

# Save the figure so you can inspect it
plt.savefig("../data/salary_distribution.png")
print("Saved plot to ../data/salary_distribution.png")

#%%
# Step 6d: numeric summary of Salary
print("\n=== Salary summary statistics ===")
print(hitters["Salary"].describe().to_string())

#%%
import matplotlib.pyplot as plt

# Scatter plot: Salary vs FPPG
plt.figure()
plt.scatter(hitters["Salary"], hitters["FPPG"], alpha=0.5)
plt.title("Salary vs. FPPG")
plt.xlabel("Salary")
plt.ylabel("FPPG")

# Save the scatter for inspection
plt.savefig("../data/salary_vs_fppg.png")
print("Saved plot to ../data/salary_vs_fppg.png")

#%%
import numpy as np
import matplotlib.pyplot as plt

# Compute log-salary
hitters["log_Salary"] = np.log(hitters["Salary"])

# Scatter: log(Salary) vs. FPPG
plt.figure()
plt.scatter(hitters["log_Salary"], hitters["FPPG"], alpha=0.5)
plt.title("log(Salary) vs. FPPG")
plt.xlabel("log(Salary)")
plt.ylabel("FPPG")
plt.savefig("../data/log_salary_vs_fppg.png")
print("Saved plot to ../data/log_salary_vs_fppg.png")

#%%
# Step 7b: correlation of log_Salary with FPPG
corr_log = hitters["log_Salary"].corr(hitters["FPPG"])
print(f"\nPearson correlation between log_Salary and FPPG: {corr_log:.4f}")










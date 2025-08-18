import pandas as pd

# Load data
pitcher_file = "../data/fd_pitcher_features_enriched.csv"
mapping_file = "../data/team_name_map.csv"

df = pd.read_csv(pitcher_file, low_memory=False)
df_map = pd.read_csv(mapping_file)

# Try possible column names
team_col = None
for col in ["team", "team_name", "team_x"]:
    if col in df.columns:
        team_col = col
        break

if team_col is None:
    raise ValueError("ERROR: Could not find a team column in the pitcher data.")

# Standardize casing
df[team_col] = df[team_col].astype(str).str.strip().str.lower()
df_map["from"] = df_map["from"].astype(str).str.strip().str.lower()

# Identify missing mappings
teams_in_data = set(df[team_col].unique())
teams_mapped = set(df_map["from"].unique())
missing_teams = sorted(teams_in_data - teams_mapped)

# Show and optionally append
if missing_teams:
    print("\n Missing team mappings:")
    for team in missing_teams:
        print(f"- {team}")

    df_missing = pd.DataFrame({"from": missing_teams, "to": [""] * len(missing_teams)})
    df_combined = pd.concat([df_map, df_missing], ignore_index=True)
    df_combined.to_csv(mapping_file, index=False)
    print(f"\nSUCCESS: Appended missing teams to {mapping_file}  please complete the 'to' column.")
else:
    print("SUCCESS: All teams are already mapped.")

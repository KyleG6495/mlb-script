import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("🔄 Loading all feature files...")

# Load base files (what you already have)
hitters_base = pd.read_csv("../data/today_hitter_features_merged.csv")
pitchers_base = pd.read_csv("../data/pitcher_features_merged.csv")

# Load additional feature files
hitter_season = pd.read_csv("../data/today_hitter_features.csv")
hitter_rolling = pd.read_csv("../data/hitter_rolling_5game_features.csv")
weather_park = pd.read_csv("../data/merged_weather_park.csv")
hitter_team_map = pd.read_csv("../data/hitter_team_map.csv")

print(f"📊 Base hitters: {hitters_base.shape}")
print(f"📊 Season features: {hitter_season.shape}")  
print(f"📊 Rolling features: {hitter_rolling.shape}")
print(f"📊 Weather/park: {weather_park.shape}")
print(f"📊 Team mapping: {hitter_team_map.shape}")

# Filter rolling data to most recent date FIRST
from datetime import datetime, timedelta
recent_date = hitter_rolling['date'].max()
print(f"🗓️ Using rolling features from: {recent_date}")
hitter_rolling_recent = hitter_rolling[hitter_rolling['date'] == recent_date].copy()

# NOW check what columns are actually available
print("\n🔍 Available columns in season data:")
print("Season columns:", hitter_season.columns.tolist())
print("\nRolling columns:", hitter_rolling_recent.columns.tolist())

print("🔄 Merging all features using PLAYER NAMES...")

# Start with base data and filter to hitters only  
enhanced_hitters = hitters_base[hitters_base['Position'] != 'P'].copy()
print(f"📊 Filtered to hitters: {enhanced_hitters.shape}")

# Create standardized names for matching
def standardize_name(name):
    """Standardize player names for matching"""
    if pd.isna(name):
        return ""
    return str(name).lower().strip().replace(".", "").replace(" jr", "").replace(" sr", "")

# Standardize names in all datasets
enhanced_hitters['name_std'] = enhanced_hitters['Nickname'].apply(standardize_name)
hitter_season['name_std'] = hitter_season['name'].apply(standardize_name)
hitter_rolling_recent['name_std'] = hitter_rolling_recent['name'].apply(standardize_name)

# Check name matching
fd_names = set(enhanced_hitters['name_std'].unique())
season_names = set(hitter_season['name_std'].unique())
rolling_names = set(hitter_rolling_recent['name_std'].unique())

print(f"🔗 NAME MATCHING ANALYSIS:")
print(f"FD ∩ Season: {len(fd_names & season_names)}/{len(fd_names)} name matches")
print(f"FD ∩ Rolling: {len(fd_names & rolling_names)}/{len(fd_names)} name matches")

# Merge season data by names (aggregate stats per player)
print("🔄 Merging season data by names...")
season_agg = hitter_season.groupby('name_std').agg({
    'atBats': 'sum', 'hits': 'sum', 'doubles': 'sum', 'triples': 'sum',
    'homeRuns': 'sum', 'rbi': 'sum', 'runs': 'sum', 'baseOnBalls': 'sum', 
    'strikeOuts': 'sum'
}).reset_index()

enhanced_hitters = enhanced_hitters.merge(
    season_agg,
    on='name_std',
    how='left',
    suffixes=('', '_season')
)

# Merge rolling data by names (most recent stats)
print("🔄 Merging rolling data by names...")
rolling_latest = hitter_rolling_recent.sort_values('date').groupby('name_std').last().reset_index()
rolling_cols = ['name_std', 'hits', 'atBats', 'homeRuns', 'rbi', 'baseOnBalls', 'strikeOuts']
available_rolling_cols = [col for col in rolling_cols if col in rolling_latest.columns]

enhanced_hitters = enhanced_hitters.merge(
    rolling_latest[available_rolling_cols],
    on='name_std',
    how='left',
    suffixes=('', '_rolling')
)

# Weather/park data (skip for now since it needs game_pk matching)
print("⚠️ Skipping weather data (requires game_pk matching)")

print(f"✅ Enhanced hitters shape after name merging: {enhanced_hitters.shape}")

# Convert statistical columns to numeric - with debugging
stat_columns = ['FPPG', 'Salary', 'atBats', 'hits', 'homeRuns', 'rbi', 'runs', 
               'baseOnBalls', 'strikeOuts', 'doubles', 'triples', 'stolenBases',
               'atBats_season', 'hits_season', 'homeRuns_season', 'rbi_season',
               'atBats_rolling', 'hits_rolling', 'homeRuns_rolling', 'rbi_rolling',
               'temperature', 'wind_speed', 'park_factor']

print("🔄 Converting columns to numeric...")
for col in stat_columns:
    if col in enhanced_hitters.columns:
        print(f"Converting {col}: {enhanced_hitters[col].dtype} → numeric")
        enhanced_hitters[col] = pd.to_numeric(enhanced_hitters[col], errors='coerce')

# Check data types after conversion
print("\n📊 Data types after conversion:")
for col in enhanced_hitters.columns:
    if enhanced_hitters[col].dtype in ['object', 'int64', 'float64']:
        print(f"{col}: {enhanced_hitters[col].dtype}")

# Calculate advanced stats BEFORE filtering to numeric
print("\n🔄 Creating advanced batting statistics...")

# Batting averages
if 'hits_season' in enhanced_hitters.columns and 'atBats_season' in enhanced_hitters.columns:
    enhanced_hitters['season_avg'] = enhanced_hitters['hits_season'] / enhanced_hitters['atBats_season'].replace(0, np.nan)
    print("✅ Created season_avg")

if 'hits_rolling' in enhanced_hitters.columns and 'atBats_rolling' in enhanced_hitters.columns:
    enhanced_hitters['rolling_avg'] = enhanced_hitters['hits_rolling'] / enhanced_hitters['atBats_rolling'].replace(0, np.nan)
    print("✅ Created rolling_avg")

# Power stats
if 'homeRuns_season' in enhanced_hitters.columns and 'atBats_season' in enhanced_hitters.columns:
    enhanced_hitters['season_hr_rate'] = enhanced_hitters['homeRuns_season'] / enhanced_hitters['atBats_season'].replace(0, np.nan)
    print("✅ Created season_hr_rate")

if 'homeRuns_rolling' in enhanced_hitters.columns and 'atBats_rolling' in enhanced_hitters.columns:
    enhanced_hitters['rolling_hr_rate'] = enhanced_hitters['homeRuns_rolling'] / enhanced_hitters['atBats_rolling'].replace(0, np.nan)
    print("✅ Created rolling_hr_rate")

# Additional rate stats
if 'rbi_season' in enhanced_hitters.columns and 'atBats_season' in enhanced_hitters.columns:
    enhanced_hitters['season_rbi_rate'] = enhanced_hitters['rbi_season'] / enhanced_hitters['atBats_season'].replace(0, np.nan)
    print("✅ Created season_rbi_rate")

print(f"\n📊 Enhanced hitters shape after cleanup: {enhanced_hitters.shape}")

# ✅ PRESERVE ESSENTIAL PLAYER IDENTIFICATION COLUMNS
essential_columns = ['Nickname', 'Team', 'Opponent', 'Position', 'Roster Position', 'Game']

# Select specific columns we want for analysis (INCLUDE ESSENTIAL COLUMNS)
analysis_columns = [
    # ✅ ESSENTIAL PLAYER INFO (MUST KEEP!)
    'Nickname', 'Team', 'Opponent', 'Position', 'Roster Position', 'Game',
    # Fantasy/salary info
    'FPPG', 'Salary', 'Played', 'player_id',
    # Current game stats (from base data)
    'atBats', 'hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 'strikeOuts', 
    'doubles', 'triples', 'stolenBases',
    # Season stats (with _season suffix)
    'atBats_season', 'hits_season', 'homeRuns_season', 'rbi_season',
    'baseOnBalls_season', 'strikeOuts_season', 'doubles_season', 'triples_season',
    # Rolling stats (with _rolling suffix)  
    'atBats_rolling', 'hits_rolling', 'homeRuns_rolling', 'rbi_rolling', 
    'baseOnBalls_rolling', 'strikeOuts_rolling',
    # Weather/park factors (with correct suffixes)
    'temperature_x', 'wind_speed_x', 'park_factor_x', 
    'temperature_y', 'wind_speed_y', 'park_factor_y',
    # Advanced calculated stats
    'season_avg', 'rolling_avg', 'season_hr_rate', 'rolling_hr_rate', 'season_rbi_rate'
]

print(f"🔍 Looking for these columns: {analysis_columns}")

# Debug the selection process
available_cols = []
missing_cols = []

for col in analysis_columns:
    if col in enhanced_hitters.columns:
        available_cols.append(col)
        print(f"✅ FOUND: {col}")
    else:
        missing_cols.append(col)
        print(f"❌ MISSING: {col}")

print(f"\n📊 SUMMARY:")
print(f"Available columns ({len(available_cols)}): {available_cols}")
print(f"Missing columns ({len(missing_cols)}): {missing_cols}")

# Create final dataset with available columns
final_dataset = enhanced_hitters[available_cols].copy()

# Convert ONLY the statistical columns to numeric (preserve text columns)
numeric_columns = ['FPPG', 'Salary', 'Played', 'player_id'] + [col for col in available_cols if any(stat in col for stat in ['atBats', 'hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 'strikeOuts', 'doubles', 'triples', 'stolenBases', 'temperature', 'wind_speed', 'park_factor', 'avg', 'rate'])]

print(f"\n🔄 Converting statistical columns to numeric:")
for col in numeric_columns:
    if col in final_dataset.columns:
        final_dataset[col] = pd.to_numeric(final_dataset[col], errors='coerce')
        print(f"✅ Converted {col} to numeric")

print(f"\n🎯 Final enhanced dataset: {final_dataset.shape}")
print(f"📋 Selected analysis columns: {list(final_dataset.columns)}")

# Enhanced correlation analysis (only on numeric columns)
numeric_cols_for_corr = [col for col in final_dataset.columns if final_dataset[col].dtype in ['int64', 'float64']]
if 'FPPG' in numeric_cols_for_corr:
    corr_data = final_dataset[numeric_cols_for_corr]
    corr_target = corr_data.corr()["FPPG"].abs().sort_values(ascending=False)
    print("\n=== TOP 20 FEATURES BY FPPG CORRELATION ===")
    print(corr_target.head(20).to_string())

# Save enhanced dataset WITH PLAYER INFO
final_dataset.to_csv("../data/hitters_enhanced_features_with_info.csv", index=False)
print("✅ Saved enhanced features with player info to: ../data/hitters_enhanced_features_with_info.csv")

print("🎉 Enhanced EDA complete!")

# Show sample of final dataset
print(f"\n🔍 Sample data inspection:")
print("Essential columns preserved:")
essential_in_final = [col for col in essential_columns if col in final_dataset.columns]
print(f"✅ Player info columns: {essential_in_final}")

sample_display = final_dataset[essential_in_final + ['FPPG', 'Salary', 'season_avg', 'homeRuns_season']].head()
print(sample_display)










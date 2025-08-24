# MLB AUTOMATION SYSTEM - COMPLETE GUIDE

## Table of Contents
1. [System Overview](#system-overview)
2. [Batch File Descriptions](#batch-file-descriptions)
3. [Recommended Workflow](#recommended-workflow)
4. [Key Differences Between Scripts](#key-differences)
5. [Which Scripts to Run](#which-scripts-to-run)

---

## System Overview

Your MLB automation system consists of 8 batch files that handle different aspects of baseball analytics:

- **Data Collection** (Pipeline)
- **DFS Lineup Optimization** (Multiple versions)
- **Prop Betting Analysis** (Multiple versions)
- **Performance Analysis** (Backtesting)

Think of it as a factory assembly line where each step builds on the previous one.

---

## Batch File Descriptions

### 1. `1_DATA_PIPELINE.bat` 📊
**Purpose:** The foundation - collects all fresh data needed for analysis

**What it does:**
- Downloads today's MLB games and player information
- Scrapes player statistics from websites
- Builds weather data for all ballparks
- Creates player feature files for machine learning
- Updates FanDuel slate with today's players and salaries

**Time:** 35-45 minutes
**When to run:** Once daily, first thing in the morning
**Output files:**
- `fd_slate_today.csv` (FanDuel players/salaries)
- `fd_hitter_features_final.csv` (Hitter statistics)
- `fd_pitcher_features_final.csv` (Pitcher statistics)
- Weather and park factor files

**Think of it as:** Getting all the ingredients before cooking

---

### 2. `2_DFS_MODELS.bat` 🏆
**Purpose:** Creates optimized FanDuel lineups using machine learning

**What it does:**
- Uses your trained ML models to predict player performance
- Generates different types of lineups:
  - 5 Cash Game lineups (safe, high-floor players)
  - 8 Small Tournament lineups (balanced risk/reward)
  - 7 Large GPP lineups (high-risk, high-reward)
- Ensures lineups meet FanDuel requirements ($35,000 salary cap)
- Creates backup lineups if batting orders aren't posted yet

**Time:** 8-12 minutes
**Prerequisites:** Must run `1_DATA_PIPELINE.bat` first
**Output files:**
- `enhanced_ml_dfs_lineups_*.csv` (Main optimized lineups)
- `fanduel_submission_*.csv` (Ready to upload to FanDuel)
- `ranked_lineups_*.csv` (Analysis of best lineups by contest type)

**Think of it as:** The main chef creating the menu

---

### 3. `2B_ENHANCED_DFS.bat` 🚀
**Purpose:** Advanced version of DFS optimization with game simulation

**What it does:**
- Runs enhanced DFS with game state simulation
- More sophisticated projections than standard DFS
- Takes 10-15 minutes (longer than standard)

**Difference from 2_DFS_MODELS.bat:**
- More advanced algorithms
- Game state simulation
- Potentially higher scoring lineups
- Takes longer to run

**Think of it as:** The master chef's special menu

---

### 4. `3_PROP_MODELS.bat` 💰
**Purpose:** Full prop betting analysis across multiple platforms

**What it does:**
- Runs your calibrated automated betting system (with Logan Webb fixes!)
- Scrapes PrizePicks for current prop lines
- Scrapes Underdog Fantasy for current prop lines
- Analyzes betting opportunities across platforms
- Generates combination strategies
- Provides Kelly Criterion bet sizing

**Time:** 10-15 minutes
**Prerequisites:** Must run `1_DATA_PIPELINE.bat` first
**Output files:**
- `betting_opportunities_*.csv` (Individual prop bets)
- `optimal_combinations_today.csv` (Best prop combinations)
- `betting_report_*.txt` (Summary analysis)
- Platform-specific analysis files

**Think of it as:** The full-service betting advisor

---

### 5. `3_SIMPLIFIED_PROPS.bat` 💰🎯
**Purpose:** Streamlined version focusing on your calibrated system

**What it does:**
- Runs ONLY your working automated betting system
- Includes all the Logan Webb role-based fixes we implemented
- Minimal scraping (less likely to fail)
- Focuses on high-confidence predictions

**Time:** 5-10 minutes (faster than full prop analysis)
**Difference from 3_PROP_MODELS.bat:**
- Simpler, more reliable
- Uses only your calibrated system
- Less comprehensive but more stable
- Better for daily use

**Think of it as:** The reliable betting advisor you can count on

---

### 6. `3_BACKTEST_ANALYSIS.bat` 📊
**Purpose:** Analyzes how well your predictions performed yesterday

**What it does:**
- Compares your DFS lineup predictions vs actual points scored
- Analyzes your prop bet predictions vs actual results
- Calculates win rates, ROI, and accuracy metrics
- Identifies which models/strategies work best
- Generates performance reports

**Time:** 3-5 minutes
**Prerequisites:** Need yesterday's lineups and betting picks
**Output files:**
- `dfs_performance_analysis_*.csv` (Lineup accuracy)
- `prizepicks_backtest_*.csv` (Prop betting results)
- `daily_performance_summary_*.html` (Visual report)

**Think of it as:** The performance review meeting

---

### 7. `4_ENHANCED_MODELS.bat` 🚀
**Purpose:** Advanced versions of both DFS and prop betting

**What it does:**
- Runs enhanced ceiling optimization for DFS
- Targets 210+ point lineups for tournaments
- Enhanced prop predictions with stat adjustments
- Aims for 70%+ win rates on props
- Creates high-variance, high-reward strategies

**Time:** Variable (depends on available data)
**Difference from standard models:**
- More aggressive optimization
- Higher ceiling potential
- More complex algorithms
- Best for experienced users

**Think of it as:** The experimental kitchen trying new recipes

---

### 8. Empty Files: `5_ULTIMATE_ENSEMBLE.bat` & `6_WEATHER_ENHANCED_ENSEMBLE.bat`
**Status:** These files exist but are empty
**Purpose:** Likely planned for future enhancements

---

## Key Differences Between Scripts

### DFS Scripts Comparison:
| Script | Speed | Complexity | Best For |
|--------|-------|------------|----------|
| `2_DFS_MODELS.bat` | Medium | Standard | Daily use, reliable lineups |
| `2B_ENHANCED_DFS.bat` | Slow | High | Special tournaments, max performance |

### Prop Betting Scripts Comparison:
| Script | Speed | Reliability | Features | Best For |
|--------|-------|-------------|----------|----------|
| `3_PROP_MODELS.bat` | Slow | Medium | Full analysis, all platforms | Complete daily analysis |
| `3_SIMPLIFIED_PROPS.bat` | Fast | High | Core system only | Daily reliable betting |
| `4_ENHANCED_MODELS.bat` | Variable | Medium | Advanced strategies | Experienced users |

---

## Recommended Workflow

### For Beginners (Most Reliable):
```
1. Run 1_DATA_PIPELINE.bat (morning)
2. Run 2_DFS_MODELS.bat (for lineups)
3. Run 3_SIMPLIFIED_PROPS.bat (for betting)
4. Run 3_BACKTEST_ANALYSIS.bat (next day review)
```

### For Advanced Users (Maximum Performance):
```
1. Run 1_DATA_PIPELINE.bat (morning)
2. Run 2B_ENHANCED_DFS.bat (advanced lineups)
3. Run 3_PROP_MODELS.bat (full prop analysis)
4. Run 4_ENHANCED_MODELS.bat (experimental strategies)
5. Run 3_BACKTEST_ANALYSIS.bat (performance review)
```

### Time-Constrained Schedule:
```
1. Run 1_DATA_PIPELINE.bat (essential)
2. Run 3_SIMPLIFIED_PROPS.bat (quickest betting analysis)
```

---

## Which Scripts to Run

### ✅ MUST RUN DAILY:
- **`1_DATA_PIPELINE.bat`** - Essential foundation for everything else

### 🎯 CHOOSE ONE DFS OPTION:
- **`2_DFS_MODELS.bat`** - Standard, reliable (recommended for most users)
- **`2B_ENHANCED_DFS.bat`** - Advanced, experimental (for power users)

### 💰 CHOOSE ONE PROP BETTING OPTION:
- **`3_SIMPLIFIED_PROPS.bat`** - Fast, reliable (recommended for daily use)
- **`3_PROP_MODELS.bat`** - Comprehensive analysis (for thorough research)

### 📊 OPTIONAL ENHANCEMENTS:
- **`4_ENHANCED_MODELS.bat`** - Only if you want experimental strategies
- **`3_BACKTEST_ANALYSIS.bat`** - Only for performance tracking

### ❌ DON'T NEED TO RUN:
- **`5_ULTIMATE_ENSEMBLE.bat`** - Empty file
- **`6_WEATHER_ENHANCED_ENSEMBLE.bat`** - Empty file

---

## Summary

**Minimum Daily Workflow (30 minutes total):**
1. `1_DATA_PIPELINE.bat` (35-45 min)
2. `3_SIMPLIFIED_PROPS.bat` (5-10 min)

**Recommended Daily Workflow (50 minutes total):**
1. `1_DATA_PIPELINE.bat` (35-45 min)
2. `2_DFS_MODELS.bat` (8-12 min)
3. `3_SIMPLIFIED_PROPS.bat` (5-10 min)

**Power User Workflow (70+ minutes):**
1. `1_DATA_PIPELINE.bat` (35-45 min)
2. `2B_ENHANCED_DFS.bat` (10-15 min)
3. `3_PROP_MODELS.bat` (10-15 min)
4. `4_ENHANCED_MODELS.bat` (variable)

**Key Point:** You don't need to run all scripts. Pick the combination that fits your time and experience level. The data pipeline is the only essential component - everything else builds on that foundation.

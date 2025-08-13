# DAILY MLB DFS WORKFLOW - QUICK REFERENCE
=============================================

## 🎯 PROBLEM WE SOLVED
- **Issue**: Shane Bieber (IL-Elbow) was appearing in DFS lineups with impossible projections
- **Root Cause**: FanDuel slate includes injured players marked as "IL" in Injury Indicator column
- **Solution**: Filter out all IL players before generating lineups

## 🚀 DAILY WORKFLOW (5 STEPS)

### STEP 1: Update FanDuel Slate ⚡ CRITICAL
```
Download today's FanDuel slate → fd_current_slate/fd_slate_today.csv
```

### STEP 2: Copy Complete Slate ⚡ CRITICAL  
```powershell
Copy-Item "fd_current_slate/fd_slate_today.csv" "data/fd_slate_today.csv" -Force
```

### STEP 3: Filter Injured Players ⚡ CRITICAL
```bash
python filter_todays_pitchers.py
```
**THIS IS THE KEY STEP** - Removes Shane Bieber and ~174 other IL players

### STEP 4: Run Data Pipeline ⚡ CRITICAL
```bash
1_DATA_PIPELINE.bat
```
Builds all hitter/pitcher features with weather/park factors (20 steps)

### STEP 5: Generate Enhanced DFS ⚡ CRITICAL
```bash
python run_game_state_enhanced_dfs.py
```
Creates 20 optimized lineups with 2000 simulations

## 🎮 ONE-CLICK OPTION
```bash
DAILY_DFS_COMPLETE_WORKFLOW.bat
```
Runs all 5 steps automatically with error checking

## 📊 EXPECTED RESULTS
- **Total Players**: ~638 (all healthy, active players only)
- **Lineups Generated**: 20 diverse lineups
- **Top FPPG**: 135-145 range (realistic projections)
- **Strategies**: Floor, Balanced, Ceiling approaches
- **No IL Players**: Shane Bieber and other injured players completely removed

## 🔍 VALIDATION CHECKS
```bash
python DAILY_DFS_WORKFLOW.py
```
- Validates all required files exist
- Checks recent lineups for injured players
- Reports system health

## 📁 KEY FILES CREATED
```
data/game_state_enhanced_lineups_YYYYMMDD_HHMMSS.csv    ← Your final lineups
data/game_state_enhanced_projections_YYYYMMDD_HHMMSS.csv ← Enhanced projections
data/fd_pitcher_features_final.csv                       ← Filtered healthy pitchers
```

## ⚠️ CRITICAL SUCCESS FACTORS
1. **Always run filter_todays_pitchers.py** before generating lineups
2. **Verify Shane Bieber is NOT in results** - grep for "Shane.*Bieber" in lineup files
3. **Check pitcher count** - Should be ~595 healthy pitchers, not 769+ with injured
4. **Realistic projections** - Top FPPG should be 135-145, not 200+ (sign of bad data)

## 🛠️ TROUBLESHOOTING
**If Shane Bieber appears in lineups:**
```bash
# 1. Check if he's in the source slate (he shouldn't be unless marked IL)
grep -i "bieber" data/fd_slate_today.csv

# 2. Re-run the filtering script
python filter_todays_pitchers.py

# 3. Verify he's removed from pitcher features
grep -i "bieber" data/fd_pitcher_features_final.csv

# 4. Regenerate lineups
python run_game_state_enhanced_dfs.py
```

**Daily Success Metrics:**
- ✅ No injured players in lineups
- ✅ Realistic FPPG projections (not 200+)
- ✅ Proper player counts (~595 pitchers, not 769+)
- ✅ All salary caps properly utilized
- ✅ Multiple diverse lineup strategies

## 📈 SYSTEM BENEFITS
- **Clean Data**: Only active, healthy players
- **Advanced Modeling**: 2000 simulations with ML projections
- **Weather Integration**: Park factors and weather conditions
- **Ownership Projections**: Contest-aware lineup construction
- **Strategy Diversity**: Floor/Balanced/Ceiling approaches for different contest types

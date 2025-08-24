# 🎯 KYLE'S OPTIMIZED DAILY DFS CHECKLIST
## Complete Workflow with Clean Data Integration

### ⏰ **TIMING: 8:00-9:30 AM Daily**

---

## 🚀 **OPTION 1: ONE-CLICK WORKFLOW (RECOMMENDED)**
```powershell
# Navigate to DAILY_RUNNERS
cd "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"

# Run the complete optimized workflow
.\KYLE_OPTIMIZED_DAILY_WORKFLOW.bat
```

---

## 📋 **OPTION 2: MANUAL STEP-BY-STEP**

### **STEP 0: 🧹 DATA CLEANING (CRITICAL FIRST!)**
```powershell
cd "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
python CLEAN_SLATE_DATA.py
```
**Result**: Removes Shane Bieber + 346 other injured players

---

### **STEP 1: 📊 CORE DATA PIPELINE**
```powershell
cd "DAILY_RUNNERS"
.\1_DATA_PIPELINE.bat
```
**What it does**: Processes raw MLB data, creates features

---

### **STEP 2: 🎯 DFS MODELS**
```powershell
.\2_DFS_MODELS.bat
```
**What it does**: Builds projections, filters players

---

### **STEP 3: 🎰 VEGAS INTEGRATION**
```powershell
cd ".."
python VEGAS_ODDS_INTEGRATOR.py
```
**What it does**: Adds betting lines and totals

---

### **STEP 4: 👥 CLEAN OWNERSHIP PROJECTIONS**
```powershell
python ADVANCED_OWNERSHIP_PROJECTIONS.py
```
**What it does**: Creates ownership predictions using CLEAN data (no injured players)

---

### **STEP 5: 🧠 ADVANCED RESEARCH SUITE**
```powershell
python ADVANCED_STACK_OPTIMIZER.py
python advanced_correlation_analyzer.py
python ownership_leverage_analyzer.py
python ENHANCED_GPP_STACKING_STRATEGY_FIXED.py
```
**What it does**: 
- Elite stacks (STL, BAL, BOS)
- Correlation insights (+25% edges)
- High leverage plays (clean data only)
- GPP tournament strategy

---

### **STEP 6: 🏆 ELITE LINEUPS**
```powershell
python ELITE_TOURNAMENT_WITH_OWNERSHIP.py
```
**What it does**: Creates optimized tournament lineups

---

### **STEP 7: ⚡ ENHANCED MODELS (OPTIONAL)**
```powershell
cd "DAILY_RUNNERS"
.\4_ENHANCED_MODELS.bat
```
**When to use**: For high-stakes tournaments

---

### **STEP 8: 🚀 DASHBOARD LAUNCH**
```powershell
cd ".."
python COMPLETE_ELITE_DFS_DASHBOARD.py
```
**What it shows**: Clean data analysis with GPP stacking tab

---

## 📊 **OPTIONAL: PROPS & BACKTESTING**

### **Yesterday's Analysis**
```powershell
python backtest_yesterday_OPTIMIZED.py
python comprehensive_backtest_analysis.py
python collect_actual_results_enhanced.py
python elite_backtest_validator.py
```

---

## ✅ **DAILY CHECKLIST VERIFICATION**

### **Before Starting:**
- [ ] Downloaded fresh FanDuel slate to `fd_slate_today.csv`
- [ ] Starting lineups available
- [ ] Weather data current

### **After STEP 0 (Data Cleaning):**
- [ ] Clean slate shows ~1,472 players (not 1,819)
- [ ] Shane Bieber NOT in clean slate
- [ ] Backup created with timestamp

### **After STEP 4 (Ownership):**
- [ ] New ownership file created today
- [ ] File shows current date timestamp
- [ ] No injured players in ownership projections

### **After STEP 5 (Research):**
- [ ] Stack recommendations show only active teams
- [ ] Leverage analysis shows NO Shane Bieber
- [ ] GPP strategy shows 26 active teams

### **Final Verification:**
- [ ] Dashboard shows clean player counts
- [ ] Elite Leverage section has NO injured players
- [ ] All analysis files dated today

---

## 🚨 **TROUBLESHOOTING**

### **If Shane Bieber Still Appears:**
1. Check if `fd_slate_today_clean.csv` exists
2. Verify ownership projections are dated today
3. Restart dashboard after cleaning

### **If Player Counts Look Wrong:**
- Clean slate: ~1,472 players
- Original slate: ~1,819 players
- Difference: ~347 injured players removed

### **If Scripts Fail:**
1. Ensure you're in correct directory
2. Check that slate file exists
3. Run `python CLEAN_SLATE_DATA.py` first

---

## 🎯 **SUCCESS METRICS**
- ✅ No injured players in any analysis
- ✅ All data files dated today
- ✅ Dashboard shows "clean" indicators
- ✅ Leverage plays exclude Shane Bieber
- ✅ Ready for lineup building by 9:30 AM

---

## 📱 **QUICK REFERENCE**
- **One-click**: `KYLE_OPTIMIZED_DAILY_WORKFLOW.bat`
- **Clean data**: Always starts with `CLEAN_SLATE_DATA.py`
- **Verification**: Check for "clean" indicators in outputs
- **Emergency**: Use `MASTER_RESEARCH_SUITE.bat` if main workflow fails

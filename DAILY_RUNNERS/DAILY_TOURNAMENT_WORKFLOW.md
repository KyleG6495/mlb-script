# 🏆 DAILY TOURNAMENT WORKFLOW
## Complete Process After Data Pipeline

### 📋 **PREREQUISITES (Must be done first)**
1. ✅ Run your data pipeline (`1_DATA_PIPELINE.bat`)
2. ✅ Upload fresh `fd_slate_today.csv` to `/fd_current_slate/` folder
3. ✅ Verify slate has today's games and proper salary/projection data

---

## 🎯 **DAILY TOURNAMENT PROCESS**

### **OPTION A: One-Click Solution** ⭐ **(RECOMMENDED)**
```bash
# Run this single command after data pipeline:
DAILY_RUNNERS\DAILY_TOURNAMENT_GENERATOR.bat
```

**What it does:**
- ✅ Checks for injured players (IL status)
- ✅ Creates IL-free player slate
- ✅ Gets confirmed starters via RotoWire
- ✅ Generates 8+ championship lineups (116-130 FPPG)
- ✅ Runs Monte Carlo tournament analysis
- ✅ Creates FanDuel-ready submission files

---

### **OPTION B: Manual Step-by-Step**
If you want more control, run these individually:

#### **Step 1: Check for Injuries** 🏥
```bash
python -c "
import pandas as pd
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
il_count = len(df[df['Injury Indicator'] == 'IL'])
print(f'⚠️ Found {il_count} injured players to remove')
"
```

#### **Step 2: Create Healthy-Only Slate** 
```bash
python -c "
import pandas as pd
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
healthy = df[df['Injury Indicator'] != 'IL']
healthy.to_csv('../data/fd_slate_NO_IL_PLAYERS.csv', index=False)
print(f'✅ Saved {len(healthy)} healthy players')
"
```

#### **Step 3: Generate Tournament Lineups** 🏆
```bash
python MULTIPLE_CHAMPIONSHIP_BUILDER.py
```

#### **Step 4: Validate Lineups** 🔍
```bash
python QUICK_LINEUP_CHECK.py
```

---

## 📁 **OUTPUT FILES** (Generated Daily)

### **FanDuel Submission Files:**
```
/data/CHAMPIONSHIP_LINEUP_1_Elite_P_1_YYYYMMDD_HHMMSS.csv
/data/CHAMPIONSHIP_LINEUP_2_Elite_P_2_YYYYMMDD_HHMMSS.csv
/data/CHAMPIONSHIP_LINEUP_3_Value_P_1_YYYYMMDD_HHMMSS.csv
... (8+ files total)
```

### **Summary & Analysis:**
```
/data/CHAMPIONSHIP_LINEUPS_SUMMARY_YYYYMMDD_HHMMSS.csv
/data/fd_slate_NO_IL_PLAYERS.csv (healthy players only)
```

---

## 🎯 **TOURNAMENT STRATEGY**

### **Lineup Distribution:**
- **Elite Pitcher Builds (3 lineups):** High-salary aces + value hitters
- **Value Pitcher Builds (2 lineups):** Mid-tier pitchers + premium hitters  
- **Contrarian Builds (3+ lineups):** Lower-owned players with upside

### **Expected Performance:**
- **Best Lineup:** 125-130+ FPPG
- **Average Range:** 118-125 FPPG
- **Tournament Quality:** All lineups 115+ FPPG minimum

---

## ✅ **DAILY CHECKLIST**

### **Before Generating Lineups:**
- [ ] Data pipeline completed successfully
- [ ] Fresh `fd_slate_today.csv` uploaded
- [ ] Slate contains today's games only
- [ ] Player salaries and projections look reasonable

### **After Generating Lineups:**
- [ ] Run `QUICK_LINEUP_CHECK.py` to validate
- [ ] Check no injured players (IL) in lineups
- [ ] Verify salary cap compliance (under $35,000)
- [ ] Confirm 8+ diverse tournament lineups created
- [ ] Upload individual CSV files to FanDuel

### **Tournament Submission:**
- [ ] Use ALL generated lineups for maximum coverage
- [ ] Prioritize highest-projection lineups for guaranteed prize pools
- [ ] Use contrarian builds for large-field tournaments
- [ ] Monitor injury news throughout the day

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues:**

**"Shane Bieber still in lineups"**
- ✅ **Fixed:** System now uses `fd_slate_NO_IL_PLAYERS.csv`
- ✅ All IL players automatically filtered out

**"Low projections (under 115 FPPG)"**
- Check if data pipeline updated projections
- Verify `fd_hitter_features_final.csv` and `fd_pitcher_features_final.csv` exist
- Re-run feature engineering if needed

**"Salary cap violations"**
- Should not happen with current system
- Check if player salaries in slate are corrupted
- Re-download fresh slate if needed

**"Missing confirmed starters"**
- RotoWire scraping may be down
- System will use probable starters as backup
- Check `GET_CONFIRMED_STARTERS.py` output

---

## 🎉 **SUCCESS METRICS**

### **Daily Goals:**
- ✅ Generate 8+ healthy tournament lineups
- ✅ Average projection 120+ FPPG
- ✅ Zero injured players in any lineup
- ✅ 100% salary cap compliance
- ✅ Strategic diversity across all builds

### **Tournament Performance:**
- 🎯 Target: 15%+ of lineups cash in tournaments
- 🏆 Goal: At least 1 lineup in top 10% weekly
- 💰 ROI: Positive long-term expected value

---

## 📞 **SUPPORT**

If you encounter issues:
1. Check the error logs in terminal output
2. Run `QUICK_LINEUP_CHECK.py` for validation
3. Verify input files exist and contain proper data
4. Ensure data pipeline completed successfully

**Remember:** This system automatically handles injury filtering, salary optimization, and tournament strategy. Just upload the generated CSV files to FanDuel!

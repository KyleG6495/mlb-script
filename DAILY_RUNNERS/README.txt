MLB DAILY RUNNERS - ORGANIZED SYSTEM
====================================

📁 FOLDER CONTENTS:
==================

🎯 **INDIVIDUAL RUNNERS:**
1️⃣ 1_DATA_PIPELINE.bat      - Steps 1-20: Pull & scrape fresh data (~35-45 min)
2️⃣ 2_DFS_MODELS.bat         - DFS lineup optimization (~8-12 min)  
3️⃣ 3_PROP_MODELS.bat        - Prop betting analysis (~10-15 min)

🚀 **MASTER RUNNER:**
🎯 RUN_ALL_SYSTEMS.bat       - Runs all three systems in sequence (~60-70 min)

📋 **DAILY WORKFLOW OPTIONS:**
=============================

**OPTION A - Complete Daily Analysis:**
• Double-click: RUN_ALL_SYSTEMS.bat
• Does everything: Data → DFS → Props
• Time: ~60-70 minutes
• Best for: Full daily setup

**OPTION B - Individual Systems:**
• Data refresh only: 1_DATA_PIPELINE.bat
• Lineups only: 2_DFS_MODELS.bat  
• Props only: 3_PROP_MODELS.bat
• Best for: Quick updates, targeted analysis

**OPTION C - Partial Runs:**
• Morning: 1_DATA_PIPELINE.bat
• When slate drops: 2_DFS_MODELS.bat
• When props post: 3_PROP_MODELS.bat
• Best for: Spread throughout day

🎯 **WHAT EACH SYSTEM DOES:**
============================

**1_DATA_PIPELINE.bat (Steps 1-20):**
-------------------------------------
✅ Generates hitter/pitcher games
✅ Assigns player IDs and game PKs
✅ Scrapes fresh stats from websites  
✅ Builds rolling features and aggregations
✅ Merges weather and park factors
✅ Creates final feature files

**2_DFS_MODELS.bat:**
--------------------  
✅ Finalizes hitter/pitcher features
✅ Applies real player stats
✅ Runs UNIFIED DFS optimization
✅ Creates 20 optimized lineups (3 floor + 14 balanced + 3 ceiling)
✅ Generates FanDuel submission files

**3_PROP_MODELS.bat:**
--------------------- 
✅ Runs core ML betting analysis
✅ Scrapes PrizePicks and Underdog props
✅ Analyzes EV and opportunities
✅ Creates betting recommendations with confidence intervals
✅ Generates YES/NO pick recommendations

🎯 **QUICK START:**
==================

**First Time:**
1. Double-click RUN_ALL_SYSTEMS.bat
2. Wait for completion (~60-70 min)
3. Check data\ and betting_analysis\ folders for results

**Daily Routine:**
1. Update data/fd_slate_today.csv with today's FanDuel slate
2. Run your preferred option (A, B, or C above)
3. Upload fanduel_submission_*.csv to FanDuel
4. Review prop betting picks in enhanced_betting_report_*.txt

🚀 **KEY OUTPUT FILES:**
=======================

**DFS Files:**
• fanduel_submission_*.csv ← UPLOAD TO FANDUEL
• unified_dfs_lineups_*.csv (detailed view)
• unified_dfs_summary_*.csv (overview)

**Prop Betting Files:**
• enhanced_betting_report_*.txt (YES/NO picks) 
• betting_opportunities_*.csv (detailed analysis)
• uf_mlb_picks.xlsx (Underdog Fantasy)
• prizepicks_real_ev_*.csv (PrizePicks)

💡 **ADVANTAGES:**
=================
✅ **Organized**: All runners in one place
✅ **Flexible**: Run individually or together
✅ **Clear**: Numbered sequence (1→2→3)
✅ **Efficient**: Skip steps when not needed
✅ **Complete**: Full workflow coverage

This folder contains everything you need for daily MLB analysis!

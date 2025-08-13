@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   💰 PROP BETTING MODELS & ANALYSIS
echo   Underdog Fantasy + PrizePicks Optimization
echo ========================================
echo.
echo Current directory: %CD%
echo This runs ML models for prop betting opportunities
echo Total time: ~10-15 minutes
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (RUN_DATA_PIPELINE.bat)
echo   ✅ Player features finalized
echo.
echo Press any key to start prop betting analysis...
pause
echo.

echo Step 1: Running Core ML Analysis...
python automated_betting_system.py
if errorlevel 1 goto error

echo Step 2: Scraping PrizePicks Props...
python prizepicks_mlb.py
if errorlevel 1 goto error

echo Step 3: Scraping Underdog Fantasy Props...
python underdog_fantasy_mlb.py
if errorlevel 1 goto error

echo Step 4: Analyzing Underdog Fantasy Opportunities...
python analyze_uf_props.py
if errorlevel 1 goto error

echo Step 5: Running Platform EV Analyzer...
python platform_ev_analyzer.py
if errorlevel 1 goto error

echo Step 6: Running Master Enhanced Betting System...
python master_enhanced_betting_system.py
if errorlevel 1 goto error

echo Step 7: Running Automated Betting System...
python automated_betting_system.py
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 PROP BETTING ANALYSIS COMPLETE! 
echo ========================================
echo.
echo 💰 BETTING FILES CREATED:
echo   📋 betting_report_*.txt (daily summary)
echo   📊 betting_opportunities_*.csv (detailed picks)
echo   🎯 enhanced_betting_report_*.txt (YES/NO recommendations)
echo   🎲 uf_mlb_picks.xlsx (Underdog Fantasy analysis)
echo   🎯 prizepicks_real_ev_*.csv (PrizePicks opportunities)
echo   📈 betting_analysis/betting_report_*.txt (full analysis)
echo   💎 combo_opportunities_*.csv (multi-player combos)
echo.
echo 🔥 PLATFORM BREAKDOWN:
echo   🎯 PrizePicks: High-EV individual props
echo   🎲 Underdog Fantasy: Multi-pick combinations
echo   💰 Both platforms: EV analysis with confidence intervals
echo.
echo 📊 ANALYSIS FEATURES:
echo   ✅ Ensemble ML predictions (XGBoost + RF + Neural Net)
echo   ✅ Weather & ballpark adjustments
echo   ✅ Injury & news sentiment analysis
echo   ✅ Live odds integration
echo   ✅ Kelly Criterion bankroll management
echo   ✅ Risk-adjusted portfolio optimization
echo.
echo 🎯 TODAY'S RECOMMENDATIONS:
echo   Check enhanced_betting_report_*.txt for YES/NO picks
echo   Review betting_opportunities_*.csv for detailed analysis
echo   Use combo_opportunities_*.csv for multi-pick strategies
echo.
echo 💡 BETTING STRATEGY:
echo   • Start with high-confidence single picks
echo   • Consider combo picks for higher payouts
echo   • Use Kelly Criterion for bet sizing
echo   • Monitor live odds for line movement
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in prop betting analysis!
echo Check the output above for details.
echo.
echo Troubleshooting checklist:
echo   ❓ Did you run RUN_DATA_PIPELINE.bat first?
echo   ❓ Are player features files available?
echo   ❓ Is internet connection stable for scraping?
echo   ❓ Are betting sites accessible?
echo.
echo Common issues:
echo   • PrizePicks/Underdog site changes (update scrapers)
echo   • Rate limiting (wait and retry)
echo   • Missing player mappings (check ID files)
echo   • API timeouts (retry individual steps)
echo.

:end
pause

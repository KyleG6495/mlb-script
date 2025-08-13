@echo off
echo ========================================
echo   🚀 MLB MASTER ENHANCED BETTING SYSTEM
echo   Advanced Daily Analysis Pipeline
echo ========================================
echo.

cd /d "c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo Step 1: Processing FD Slate...
python "(21)finalize_hitter_features.py"
if errorlevel 1 (
    echo ERROR in Step 1! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 1 complete!
echo.

echo Step 2: Adding Pitcher Features...
python add_pitcher_features.py
if errorlevel 1 (
    echo ERROR in Step 2! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 2 complete!
echo.

echo Step 3: Applying Real Player Stats...
python fix_prediction_features_with_real_stats.py
if errorlevel 1 (
    echo ERROR in Step 3! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 3 complete!
echo.

echo Step 4: Running ML Analysis...
python automated_betting_system.py
if errorlevel 1 (
    echo ERROR in Step 4! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 4 complete!
echo.

echo Step 5: Optimizing FanDuel Lineup...
python "23. optimize_fanduel_lineup.py"
if errorlevel 1 (
    echo ERROR in Step 5! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 5 complete!
echo.

echo Step 6: Creating FanDuel Submission...
python "24. create_fanduel_submission.py"
if errorlevel 1 (
    echo ERROR in Step 6! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 6 complete!
echo.

echo Step 7: 🚀 MASTER ENHANCED BETTING ANALYSIS...
python master_enhanced_betting_system.py
if errorlevel 1 (
    echo ERROR in Step 7! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 7 complete!
echo.

echo ========================================
echo 🏆 MASTER ENHANCED ANALYSIS COMPLETE! 
echo ========================================
echo.
echo 🎯 YOUR BETTING SYSTEM NOW INCLUDES:
echo   ✅ Ensemble ML predictions (XGBoost + RF + Neural Net)
echo   ✅ Weather & ballpark factor adjustments  
echo   ✅ Injury & news sentiment analysis
echo   ✅ Live odds integration from multiple books
echo   ✅ Combo prop optimization (2-3 player combos)
echo   ✅ Advanced confidence scoring & intervals
echo   ✅ Kelly Criterion bankroll management
echo   ✅ Clear YES/NO recommendations with EV
echo   ✅ Risk management & portfolio optimization
echo   ✅ Outlier detection & model validation
echo.
echo 📁 CHECK THESE FILES FOR RESULTS:
echo   📋 betting_report_*.txt (summary)
echo   📊 betting_opportunities_*.csv (detailed opportunities)
echo   🎯 enhanced_betting_report_*.txt (YES/NO recommendations)
echo   🏟️ fanduel_lineup_card.csv (optimal lineup)
echo   📝 fanduel_submission_names.csv (ready to submit)
echo   🔥 combo_opportunities_*.csv (multi-player combos)
echo   💰 bankroll_allocation_*.csv (optimized bet sizes)
echo   🌤️ weather_adjustments_*.csv (environmental factors)
echo   📰 injury_alerts_*.txt (player status updates)
echo.
echo 🚀 TO START LIVE MONITORING:
echo   python live_betting_runner.py
echo.
echo 💡 FOR REAL-TIME ODDS:
echo   python live_odds_scraper.py
echo ========================================
pause

@echo off
echo ========================================
echo   MLB AUTOMATED BETTING SYSTEM
echo   Quick Daily Analysis Runner
echo ========================================
echo.

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

echo Step 7: MASTER ENHANCED BETTING ANALYSIS...
python master_enhanced_betting_system.py
if errorlevel 1 (
    echo ERROR in Step 7! Check the output above.
    pause
    exit /b 1
)
echo ✅ Step 7 complete!
echo.

echo ========================================
echo 🎉 ANALYSIS COMPLETE! 
echo.
echo Check the following folder for results:
echo   betting_analysis\
echo.
echo Files created:
echo   📋 betting_report_*.txt (summary)
echo   📊 betting_opportunities_*.csv (detailed)
echo   � enhanced_betting_report_*.txt (YES/NO recommendations)
echo   �🏟️ fanduel_lineup_card.csv (optimal lineup)
echo   📝 fanduel_submission_names.csv (ready to submit)
echo.
echo To start live monitoring, run:
echo   python live_betting_runner.py
echo ========================================
pause

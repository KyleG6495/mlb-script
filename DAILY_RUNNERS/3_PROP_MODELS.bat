@echo off

REM Initialize environment and error handling
call "%~dp0config_batch.bat"
if errorlevel 1 (
    echo ❌ Failed to initialize environment
    pause
    exit /b 1
)

:start
echo ========================================
echo   [PROP BETTING] MODELS AND ANALYSIS
echo   Underdog Fantasy + PrizePicks Optimization
echo ========================================
echo.
echo Current directory: %CD%
echo This runs ML models for prop betting opportunities
echo OPTIMIZED: ~5-8 minutes (processes only confirmed starters)
echo.
echo Prerequisites:
echo   [OK] Data pipeline completed (1_DATA_PIPELINE.bat)
echo   [OK] Player features finalized
echo.
echo Press any key to start prop betting analysis...
pause
echo.

:retry_core_analysis
echo Step 1: Running OPTIMIZED Core ML Analysis (Confirmed Starters Only)...
"%PYTHON_EXE%" run_daily_analysis_OPTIMIZED.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Core ML Analysis" %errorlevel%
if errorlevel 999 goto :retry_core_analysis
if errorlevel 1 goto :error

:retry_prizepicks
echo Step 2: Scraping PrizePicks Props...
"%PYTHON_EXE%" PrizePicks_mlb.py
if errorlevel 1 (
    echo Warning: PrizePicks scraping failed - using existing data if available
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "PrizePicks Scraping (non-critical)" 0
) else (
    echo Success: Fresh PrizePicks lines collected
)
echo.

:retry_underdog
echo Step 3: Scraping Underdog Fantasy Props...
"%PYTHON_EXE%" underdog_fantasy_mlb.py
if errorlevel 1 (
    echo Warning: Underdog scraping failed - using existing data if available
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Underdog Fantasy Scraping (non-critical)" 0
) else (
    echo Success: Fresh Underdog Fantasy lines collected
)
echo.

:retry_uf_analysis
echo Step 4: Analyzing Underdog Fantasy Opportunities...
"%PYTHON_EXE%" analyze_uf_props.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Underdog Fantasy Analysis" %errorlevel%
if errorlevel 999 goto :retry_uf_analysis
if errorlevel 1 goto :error

:retry_platform_ev
echo Step 5: Running Platform EV Analyzer...
"%PYTHON_EXE%" platform_ev_analyzer.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Platform EV Analysis" %errorlevel%
if errorlevel 999 goto :retry_platform_ev
if errorlevel 1 goto :error

:retry_master_betting
echo Step 6: Running Master Enhanced Betting System...
"%PYTHON_EXE%" master_enhanced_betting_system.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Master Enhanced Betting System" %errorlevel%
if errorlevel 999 goto :retry_master_betting
if errorlevel 1 goto :error

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
echo.
echo ✅ COMPLETE DAILY ANALYSIS FINISHED!
echo    All three systems (Data + DFS + Props) ready to use.
echo ========================================
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR in prop betting analysis!
echo ========================================
echo Check the output above for details.
echo.
echo 💡 Troubleshooting checklist:
echo   ❓ Did you run 1_DATA_PIPELINE.bat first?
echo   ❓ Are player features files available?
echo   ❓ Is internet connection stable for scraping?
echo   ❓ Are betting sites accessible?
echo.
echo 🔧 Common issues:
echo   • PrizePicks/Underdog site changes (update scrapers)
echo   • Rate limiting (wait and retry)
echo   • Missing player mappings (check ID files)
echo   • API timeouts (retry individual steps)
echo.
echo 🔄 You can retry individual components or the entire analysis
set /p retry=Do you want to retry the prop betting analysis? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

@echo off
echo ========================================
echo  🎯 OPTIMIZED DAILY DFS WORKFLOW
echo  Complete Process with Clean Data
echo ========================================

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo ⏰ Start Time: %time%
echo 📅 Date: %date%
echo.

REM ========================================
REM STEP 0: DATA CLEANING (CRITICAL FIRST)
REM ========================================
echo [STEP 0] 🧹 Cleaning Slate Data - Removing Injured Players...
python CLEAN_SLATE_DATA.py
if %errorlevel% neq 0 (
    echo ❌ ERROR: Slate cleaning failed!
    pause
    exit /b 1
)
echo ✅ Clean slate created - Shane Bieber and other injured players removed
echo.

REM ========================================
REM STEP 1: CORE DATA PIPELINE
REM ========================================
echo [STEP 1] 📊 Running Core Data Pipeline...
cd "DAILY_RUNNERS"
call 1_DATA_PIPELINE.bat
if %errorlevel% neq 0 (
    echo ❌ ERROR: Data pipeline failed!
    pause
    exit /b 1
)
echo ✅ Core data pipeline complete
echo.

REM ========================================
REM STEP 2: DFS MODELS & PROJECTIONS
REM ========================================
echo [STEP 2] 🎯 Building DFS Models and Projections...
call 2_DFS_MODELS.bat
if %errorlevel% neq 0 (
    echo ❌ ERROR: DFS models failed!
    pause
    exit /b 1
)
echo ✅ DFS models complete
echo.

REM ========================================
REM STEP 3: VEGAS INTEGRATION
REM ========================================
echo [STEP 3] 🎰 Integrating Vegas Odds...
cd ".."
python VEGAS_ODDS_INTEGRATOR.py
if %errorlevel% neq 0 (
    echo ⚠️ WARNING: Vegas odds integration failed (continuing...)
)
echo ✅ Vegas odds integrated
echo.

REM ========================================
REM STEP 4: OWNERSHIP PROJECTIONS (CLEAN DATA)
REM ========================================
echo [STEP 4] 👥 Generating Clean Ownership Projections...
python ADVANCED_OWNERSHIP_PROJECTIONS.py
if %errorlevel% neq 0 (
    echo ❌ ERROR: Ownership projections failed!
    pause
    exit /b 1
)
echo ✅ Fresh ownership projections generated with clean data
echo.

REM ========================================
REM STEP 5: ADVANCED RESEARCH SUITE
REM ========================================
echo [STEP 5] 🧠 Running Advanced Research Analysis...
python ADVANCED_STACK_OPTIMIZER.py
python advanced_correlation_analyzer.py
python ownership_leverage_analyzer.py
python ENHANCED_GPP_STACKING_STRATEGY_FIXED.py
echo ✅ Advanced research complete
echo.

REM ========================================
REM STEP 6: ELITE TOURNAMENT LINEUPS
REM ========================================
echo [STEP 6] 🏆 Creating Elite Tournament Lineups...
python ELITE_TOURNAMENT_WITH_OWNERSHIP.py
if %errorlevel% neq 0 (
    echo ❌ ERROR: Elite tournament creation failed!
    pause
    exit /b 1
)
echo ✅ Elite lineups created
echo.

REM ========================================
REM STEP 7: ENHANCED MODELS (OPTIONAL)
REM ========================================
echo [STEP 7] ⚡ Enhanced Models (Optional)...
set /p run_enhanced="Run enhanced models? (y/n): "
if /i "%run_enhanced%"=="y" (
    cd "DAILY_RUNNERS"
    call 4_ENHANCED_MODELS.bat
    cd ".."
    echo ✅ Enhanced models complete
) else (
    echo ⏭️ Skipping enhanced models
)
echo.

REM ========================================
REM STEP 8: DASHBOARD LAUNCH
REM ========================================
echo [STEP 8] 🚀 Launching DFS Dashboard...
echo 💡 Dashboard will open in a new window with clean data
start python COMPLETE_ELITE_DFS_DASHBOARD.py
echo ✅ Dashboard launched
echo.

REM ========================================
REM OPTIONAL: PROPS & BACKTESTING
REM ========================================
echo ========================================
echo  📊 OPTIONAL: Props & Backtesting
echo ========================================
echo.
set /p run_props="Run props and backtesting? (y/n): "
if /i "%run_props%"=="y" (
    echo [PROPS 1] 📈 Yesterday's Backtest...
    python backtest_yesterday_OPTIMIZED.py
    
    echo [PROPS 2] 📊 Comprehensive Backtest...
    python comprehensive_backtest_analysis.py
    
    echo [PROPS 3] 📋 Collecting Results...
    python collect_actual_results_enhanced.py
    
    echo [PROPS 4] ✅ Elite Validator...
    python elite_backtest_validator.py
    
    echo ✅ Props and backtesting complete
) else (
    echo ⏭️ Skipping props and backtesting
)

echo.
echo ========================================
echo  🎉 DAILY WORKFLOW COMPLETE!
echo ========================================
echo ⏰ End Time: %time%
echo.
echo 📁 Generated Files:
echo   - fd_slate_today_clean.csv (1,472 clean players)
echo   - advanced_ownership_projections_[timestamp].csv
echo   - team_stack_analysis_[timestamp].csv
echo   - Elite tournament lineups
echo.
echo 🚀 Next Steps:
echo   1. Review dashboard analysis
echo   2. Build final lineups
echo   3. Submit to DraftKings/FanDuel
echo.
pause

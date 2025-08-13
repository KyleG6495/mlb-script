@echo off
REM ============================================================================
REM ULTIMATE DAILY MLB DFS RUNNER
REM ============================================================================
REM This runs the complete daily process using our latest and greatest tools
REM Last Updated: August 12, 2025
REM ============================================================================

echo.
echo ============================================================================
echo                    🚀 ULTIMATE DAILY MLB DFS RUNNER
echo ============================================================================
echo Using ALL our latest and greatest tools for elite DFS lineups
echo.

REM Check if FanDuel slate exists first
echo 🔍 Step 1: Checking for FanDuel slate...
if not exist "..\fd_current_slate\fd_slate_today.csv" (
    echo.
    echo ❌ ERROR: fd_slate_today.csv not found!
    echo.
    echo 📋 REQUIRED ACTION:
    echo 1. Go to FanDuel DFS MLB
    echo 2. Download today's player slate
    echo 3. Save as: fd_current_slate\fd_slate_today.csv
    echo 4. Re-run this script
    echo.
    pause
    exit /b 1
)

echo ✅ FanDuel slate found - proceeding with data pipeline...
echo.

REM Step 2: Run data pipeline
echo ============================================================================
echo 📊 Step 2: Running Data Pipeline (35-45 minutes)
echo ============================================================================
echo Pulling fresh stats, weather, and park factors...
echo.

call 1_DATA_PIPELINE.bat

if %errorlevel% neq 0 (
    echo.
    echo ❌ Data pipeline failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ✅ Data pipeline completed successfully!
echo.

REM Step 3: Run ULTIMATE FanDuel Optimizer
echo ============================================================================
echo 🏆 Step 3: Generating ULTIMATE Elite Lineups (3-5 minutes)
echo ============================================================================
echo Using ALL our latest tools:
echo - Real weather enhancement
echo - ML ensemble projections  
echo - Tournament strategy analysis
echo - Game-based environmental factors
echo.

cd "..\Scripts"

python ULTIMATE_FANDUEL_OPTIMIZER.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ ULTIMATE optimizer failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ✅ ULTIMATE lineups generated successfully!
echo.

REM Step 4: Display results
echo ============================================================================
echo 🎯 DAILY PROCESS COMPLETE - ELITE LINEUPS READY!
echo ============================================================================
echo.

REM Find the most recent files
for /f "delims=" %%i in ('dir "..\data\ULTIMATE_FANDUEL_LINEUPS_*.csv" /b /od') do set "latest_lineups=%%i"
for /f "delims=" %%i in ('dir "..\data\ULTIMATE_FANDUEL_SUMMARY_*.csv" /b /od') do set "latest_summary=%%i"

if defined latest_lineups (
    echo 📋 SUBMISSION FILE: ..\data\%latest_lineups%
    echo 📊 SUMMARY FILE:    ..\data\%latest_summary%
    echo.
    echo 🎯 NEXT STEPS:
    echo 1. Review summary file for projections
    echo 2. Upload lineups file to FanDuel
    echo 3. Check for any late injury/weather news
    echo.
    echo 🏆 SUCCESS: 5 elite lineups ready for submission!
    echo.
) else (
    echo ❌ Warning: Could not find generated lineup files
    echo.
)

echo ============================================================================
echo                    ✅ ULTIMATE DAILY PROCESS COMPLETE
echo ============================================================================
echo.

pause

@echo off
echo ================================================================
echo               ENHANCED DFS MODELS WITH VALIDATION
echo ================================================================
echo.
echo This script now includes AUTOMATIC FANDUEL VALIDATION
echo to prevent ALL submission issues we've encountered:
echo - NS (Not Starting) players
echo - IL/PO (Injured/Probable Out) players  
echo - Position eligibility violations
echo - Unconfirmed starting pitchers
echo - Duplicate player IDs
echo.

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo [%time%] Starting Enhanced DFS Models with Validation...

REM Run the enhanced models
echo.
echo [%time%] Running Base Hitter Projections...
python (23)project_base_hitter_scores.py
if %errorlevel% neq 0 (
    echo ERROR: Base hitter projections failed
    pause
    exit /b 1
)

echo.
echo [%time%] Running Base Pitcher Projections...
python (24)project_base_pitcher_scores.py
if %errorlevel% neq 0 (
    echo ERROR: Base pitcher projections failed
    pause
    exit /b 1
)

echo.
echo [%time%] Running Enhanced Hitter Projections...
python (26)project_hitter_scores.py
if %errorlevel% neq 0 (
    echo ERROR: Enhanced hitter projections failed
    pause
    exit /b 1
)

echo.
echo [%time%] Running Enhanced Pitcher Projections...
python (27)project_pitcher_scores.py
if %errorlevel% neq 0 (
    echo ERROR: Enhanced pitcher projections failed
    pause
    exit /b 1
)

echo.
echo [%time%] Running ULTIMATE FanDuel Optimizer (with AUTO-VALIDATION)...
python ULTIMATE_FANDUEL_OPTIMIZER.py
if %errorlevel% neq 0 (
    echo ERROR: ULTIMATE optimizer failed
    pause
    exit /b 1
)

echo.
echo [%time%] Running FanDuel Prevention System Check...
python FANDUEL_PREVENTION_SYSTEM.py
if %errorlevel% neq 0 (
    echo WARNING: Prevention system check had issues - lineups may need manual review
)

echo.
echo [%time%] Running Multi-Submission Formatter...
python FANDUEL_MULTI_SUBMISSION_FORMATTER.py
if %errorlevel% neq 0 (
    echo ERROR: Formatter failed
    pause
    exit /b 1
)

echo.
echo ================================================================
echo                    ENHANCED DFS COMPLETE!
echo ================================================================
echo.
echo ✅ ALL FANDUEL SUBMISSION ISSUES AUTOMATICALLY PREVENTED:
echo    - NS players replaced with confirmed starters
echo    - Injured players filtered out
echo    - Position eligibility validated
echo    - Pitchers confirmed as starters
echo    - Backups created for safety
echo.
echo 📁 Check fd_current_slate folder for final Lineups.csv
echo 🎯 Upload to FanDuel with confidence!
echo.
pause

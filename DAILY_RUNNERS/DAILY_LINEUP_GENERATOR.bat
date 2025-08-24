@echo off
echo ================================================
echo           DAILY LINEUP GENERATOR
echo ================================================
echo.
echo Generating 10 unique DFS lineups for today's slate...
echo Using ONLY confirmed starters (probable pitchers + batting order)
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and accessible
    pause
    exit /b 1
)

echo [INFO] Loading current FanDuel slate...
echo [INFO] Filtering to confirmed starters only...
echo [INFO] Building optimal lineups...

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
python DAILY_LINEUP_GENERATOR.py

if errorlevel 1 (
    echo.
    echo ERROR: Daily lineup generation failed
    echo Check the console output above for details
    pause
    exit /b 1
)

echo.
echo ================================================
echo            LINEUP GENERATION COMPLETE
echo ================================================
echo.
echo ✅ 10 unique lineups generated and saved
echo 📁 Check ../data/ folder for output files:
echo    - daily_lineups_fanduel_YYYYMMDD_HHMMSS.csv (Ready for FanDuel upload)
echo    - daily_lineup_details_YYYYMMDD_HHMMSS.csv (Analysis and player details)
echo.
echo Ready for DFS submission!
echo.

pause

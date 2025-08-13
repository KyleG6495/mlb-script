@echo off
echo ================================================
echo          ENHANCED DFS SIMULATION PIPELINE
echo ================================================
echo.
echo Starting enhanced DFS projections with game simulation...
echo This will take approximately 10-15 minutes.
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

echo [INFO] Running Game State enhanced DFS pipeline...
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
python run_game_state_enhanced_dfs.py

if errorlevel 1 (
    echo.
    echo ERROR: Enhanced DFS pipeline failed
    echo Check the log file for details: ../data/dfs_pipeline.log
    pause
    exit /b 1
) else (
    echo.
    echo SUCCESS: Enhanced DFS pipeline completed!
    echo Check the data folder for generated lineups and reports.
)

echo.
echo Enhanced DFS Pipeline Complete!
echo ================================================
pause

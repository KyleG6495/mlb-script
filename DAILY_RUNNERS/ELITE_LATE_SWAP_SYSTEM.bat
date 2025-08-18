@echo off
echo.
echo =====================================
echo  ELITE DFS LATE SWAP SYSTEM RUNNER
echo =====================================
echo.

REM Set the Python environment
set PYTHON_EXE=C:/Users/kgone/OneDrive/Personal_Information/MLB/Scripts/.venv/Scripts/python.exe

echo [STEP 1] Building Advanced Ownership Projections...
%PYTHON_EXE% ADVANCED_OWNERSHIP_PROJECTIONS.py
if %errorlevel% neq 0 goto error

echo.
echo [STEP 2] Creating Elite Tournament Lineups...
%PYTHON_EXE% ELITE_TOURNAMENT_WITH_OWNERSHIP.py
if %errorlevel% neq 0 goto error

echo.
echo [STEP 3] Starting Late Swap & Ownership Monitoring System...
echo WARNING: This will run until manually stopped!
echo Press Ctrl+C to stop the monitoring system
echo.
%PYTHON_EXE% INTEGRATED_DFS_MASTER.py

goto end

:error
echo.
echo ========================================
echo ERROR: Process failed at step %errorlevel%
echo Please check the logs for details
echo ========================================
pause
exit /b 1

:end
echo.
echo ========================================
echo  ELITE DFS SYSTEM COMPLETE!
echo ========================================
echo  Next Steps:
echo  1. Review generated lineups in fd_current_slate/
echo  2. Upload lineups to FanDuel
echo  3. Monitor system alerts for late swaps
echo ========================================
pause

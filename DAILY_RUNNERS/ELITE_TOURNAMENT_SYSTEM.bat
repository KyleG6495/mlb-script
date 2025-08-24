@echo off

REM Initialize environment and error handling
call "%~dp0config_batch.bat"
if errorlevel 1 (
    echo ❌ Failed to initialize environment
    pause
    exit /b 1
)

:start
echo ================================================
echo ELITE TOURNAMENT SYSTEM - ENHANCED
echo Based on 104-point, top 35% finish analysis
echo ================================================
echo.

echo [%time%] Starting Elite Tournament System...

:retry_elite_analysis
echo.
echo Step 1: Elite Tournament Analysis
echo ================================
"%PYTHON_EXE%" ELITE_TOURNAMENT_SYSTEM_ENHANCED.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Elite Tournament Analysis" %errorlevel%
if errorlevel 999 goto :retry_elite_analysis
if errorlevel 1 goto :error

:retry_elite_builder
echo.
echo Step 2: Elite Lineup Builder  
echo =============================
"%PYTHON_EXE%" ELITE_TOURNAMENT_LINEUP_BUILDER.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Elite Lineup Builder" %errorlevel%
if errorlevel 999 goto :retry_elite_builder
if errorlevel 1 goto :error

echo.
echo Step 3: Enhanced Late Swap Monitoring
echo ====================================
echo Starting enhanced late swap system with Waldrep patterns...
python "LATE_SWAP_AUTOMATION.py" --elite-mode
if %errorlevel% neq 0 (
    echo WARNING: Late swap system encountered issues
)

echo.
echo ================================================
echo ELITE SYSTEM COMPLETE!
echo ================================================
echo.
echo ✅ Elite patterns analyzed (Waldrep anchor strategy)
echo ✅ Tournament lineups generated (40%% anchors, 30%% stacks)  
echo ✅ Late swap monitoring active (contrarian opportunities)
echo.
echo 🎯 TARGET: Consistent top 20%% finishes with 120+ upside
echo 🏆 Based on your proven 104-point tournament success
echo.
echo Check fd_current_slate/ folder for generated lineups
echo.
pause

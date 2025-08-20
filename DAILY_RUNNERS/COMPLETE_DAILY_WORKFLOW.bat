@echo off
REM 🚀 COMPLETE DAILY MLB WORKFLOW 🚀
REM This runs the entire daily pipeline in the correct order

echo.
echo ================================================================
echo 🏆 STARTING COMPLETE DAILY MLB WORKFLOW 🏆
echo Date: %date% %time%
echo ================================================================
echo.

REM Step 1: Validate current data state
echo 🔍 STEP 1: Validating current data state...
python DAILY_DATA_VALIDATOR.py
if %errorlevel% neq 0 (
    echo ❌ Data validation failed! Check the report above.
    pause
    exit /b 1
)
echo ✅ Data validation complete
echo.

REM Step 2: Run data pipeline
echo 📊 STEP 2: Running data collection pipeline...
python 1_CONFIRMED_generate_hitter_games.py
if %errorlevel% neq 0 (
    echo ❌ Data collection failed!
    pause
    exit /b 1
)
echo ✅ Data collection complete
echo.

REM Step 3: Run DFS optimization
echo 🎯 STEP 3: Running DFS optimization...
call 2_DFS_MODELS.bat
if %errorlevel% neq 0 (
    echo ❌ DFS optimization failed!
    pause
    exit /b 1
)
echo ✅ DFS optimization complete
echo.

REM Step 4: Enhanced DFS with validation
echo 🔧 STEP 4: Running enhanced DFS optimization...
call 2B_ENHANCED_DFS.bat
if %errorlevel% neq 0 (
    echo ❌ Enhanced DFS optimization failed!
    pause
    exit /b 1
)
echo ✅ Enhanced DFS optimization complete
echo.

REM Step 5: Run prop models
echo 🎲 STEP 5: Running prop prediction models...
call 3_PROP_MODELS.bat
if %errorlevel% neq 0 (
    echo ❌ Prop models failed!
    pause
    exit /b 1
)
echo ✅ Prop models complete
echo.

REM Step 6: Run stack optimization
echo 📚 STEP 6: Running stack optimization...
python ADVANCED_STACK_OPTIMIZER.py
if %errorlevel% neq 0 (
    echo ❌ Stack optimization failed!
    pause
    exit /b 1
)
echo ✅ Stack optimization complete
echo.

REM Step 7: Final validation
echo 🔍 STEP 7: Running final validation...
python DAILY_DATA_VALIDATOR.py
if %errorlevel% neq 0 (
    echo ❌ Final validation failed! Check outputs.
    pause
    exit /b 1
)
echo ✅ Final validation complete
echo.

REM Step 8: Launch dashboard
echo 🌐 STEP 8: Launching dashboard...
echo Starting real_data_dashboard.py in background...
start "MLB Dashboard" python real_data_dashboard.py
timeout /t 3 /nobreak > nul
echo ✅ Dashboard launched at http://localhost:5004
echo.

echo ================================================================
echo 🎉 COMPLETE DAILY WORKFLOW FINISHED! 🎉
echo ================================================================
echo.
echo Your dashboard is now running with today's fresh data!
echo All files have been validated and are current.
echo.
echo 📋 Next Steps:
echo 1. Open http://localhost:5004 to view your dashboard
echo 2. Check the DFS tab for today's lineups
echo 3. Review stack recommendations
echo 4. Export lineups for FanDuel submission
echo.
echo ⚠️  Remember to download today's fd_slate_today.csv first!
echo.
pause

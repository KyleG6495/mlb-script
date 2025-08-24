@echo off
REM DAILY MLB DFS WORKFLOW - BATCH RUNNER
REM =====================================
REM Runs the complete daily DFS workflow to generate clean lineups
REM without injured players like Shane Bieber

echo.
echo ========================================
echo    DAILY MLB DFS WORKFLOW STARTING
echo ========================================
echo.

REM Step 1: Validate and copy slate data
echo STEP 1: Copying FanDuel slate data...
copy "..\fd_current_slate\fd_slate_today.csv" "..\data\fd_slate_today.csv" /Y
if errorlevel 1 (
    echo ERROR: Could not copy FanDuel slate file
    pause
    exit /b 1
)
echo ✅ Slate data copied successfully
echo.

REM Step 2: Filter out injured pitchers (CRITICAL STEP)
echo STEP 2: Filtering out injured pitchers (removing Shane Bieber and other IL players)...
python filter_todays_pitchers.py
if errorlevel 1 (
    echo ERROR: Pitcher filtering failed
    pause
    exit /b 1
)
echo ✅ Injured pitchers filtered successfully
echo.

REM Step 3: Run data pipeline
echo STEP 3: Running 20-step data pipeline...
call ..\DAILY_RUNNERS\1_DATA_PIPELINE.bat
if errorlevel 1 (
    echo ERROR: Data pipeline failed
    pause
    exit /b 1
)
echo ✅ Data pipeline completed successfully
echo.

REM Step 4: Generate enhanced DFS lineups
echo STEP 4: Generating enhanced DFS lineups with 2000 simulations...
python run_game_state_enhanced_dfs.py
if errorlevel 1 (
    echo ERROR: Enhanced DFS generation failed
    pause
    exit /b 1
)
echo ✅ Enhanced DFS lineups generated successfully
echo.

REM Step 5: Validation check
echo STEP 5: Validating results (checking for injured players)...
python DAILY_DFS_WORKFLOW.py
echo.

echo ========================================
echo    DAILY MLB DFS WORKFLOW COMPLETE!
echo ========================================
echo.
echo 📊 Check the latest game_state_enhanced_lineups_*.csv file
echo    in the data folder for your optimized lineups.
echo.
echo 🎯 Key Benefits:
echo    - Shane Bieber and other IL players removed
echo    - 2000 simulations with ML projections
echo    - Weather and park factor integration
echo    - Multiple strategy types (floor/balanced/ceiling)
echo.
pause

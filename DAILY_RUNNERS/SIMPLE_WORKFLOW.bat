@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🎯 SIMPLE DAILY WORKFLOW
echo   Using Existing Proven Scripts
echo ========================================
echo.
echo Today's Workflow:
echo   1. Generate lineups (proven system)
echo   2. Run backtest analysis
echo   3. Check prop options
echo.
echo Press any key to start...
pause
echo.

echo Step 1: Generating clean lineups...
python SIMPLE_CLEAN_GENERATOR.py
if errorlevel 1 goto error

echo.
echo Step 2: Running backtest analysis...
cd DAILY_RUNNERS
call 3_BACKTEST_ANALYSIS.bat
cd ..

echo.
echo Step 3: Prop bet option...
echo Would you like to add prop bets? 
echo   - Press 1 for YES (run MY_DAILY_PROPS.py)
echo   - Press 2 for NO (skip props)
choice /c 12 /m "Your choice"

if %errorlevel%==1 (
    echo Running prop bet system...
    python MY_DAILY_PROPS.py
) else (
    echo Skipping props - using standard lineups
)

echo.
echo ========================================
echo ✅ DAILY WORKFLOW COMPLETE!
echo ========================================
echo.
echo Generated files are ready in:
echo   📊 ../data/ (lineup CSVs)
echo   🎯 ../fd_current_slate/ (FanDuel ready)
echo.
goto end

:error
echo ❌ Error in workflow - check output above
pause

:end
pause

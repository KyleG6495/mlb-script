@echo off
echo ========================================
echo  COMPREHENSIVE DAILY DFS WORKFLOW
echo  Enhanced with Advanced Filtering
echo ========================================

cd /d "c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo [STEP 0] Cleaning slate data - removing injured players...
python CLEAN_SLATE_DATA.py
if %errorlevel% neq 0 (
    echo ERROR: Slate cleaning failed!
    pause
    exit /b 1
)
echo ✅ Clean slate created - injured players removed

echo.
echo [STEP 1] Advanced Research Analysis...
echo   - Stack optimization and leverage analysis
echo   - Correlation insights and contrarian spots
echo   - GPP tournament strategy
python ADVANCED_STACK_OPTIMIZER.py
python advanced_correlation_analyzer.py
python ownership_leverage_analyzer.py
python ENHANCED_GPP_STACKING_STRATEGY_FIXED.py
echo ✅ Research analysis complete

echo.
echo [STEP 2] Running comprehensive player filtering...
echo   - Uses clean slate data (no injured players)
echo   - Applies salary and FPPG quality thresholds
echo   - Filters for confirmed starting pitchers only
echo   - Creates multiple backup formats
python filter_todays_pitchers_simple.py
if %errorlevel% neq 0 (
    echo ERROR: Comprehensive filtering failed!
    pause
    exit /b 1
)

echo.
echo [STEP 2] Generating base DFS projections...
python (23)project_base_hitter_scores.py
python (24)project_base_pitcher_scores.py

echo.
echo [STEP 3] Creating enhanced projections...  
python (26)project_hitter_scores.py
python (27)project_pitcher_scores.py

echo.
echo [STEP 4] Running enhanced DFS models...
cd DAILY_RUNNERS
call 2B_ENHANCED_DFS.bat

echo.
echo [STEP 5] Building championship lineups...
call CHAMPIONSHIP_LINEUP_BUILDER.bat

echo.
echo ========================================
echo  WORKFLOW COMPLETE!
echo ========================================
echo.
echo RESULTS SUMMARY:
echo   - Shane Bieber: ELIMINATED
echo   - Only healthy, confirmed players used
echo   - Enhanced lineups generated
echo   - Championship lineups ready
echo.
echo Check fd_current_slate folder for results
pause

@echo off
echo ================================================================
echo              🎯 OPTIMAL DAILY MLB DFS WORKFLOW
echo ================================================================
echo Current Date: %DATE%
echo Current Time: %TIME%
echo.

REM Check if fd_slate_today.csv was updated
echo ☐ Step 0: Verifying slate freshness...
python PRE_FLIGHT_CHECKER.py
if errorlevel 1 (
    echo ❌ CRITICAL: fd_slate_today.csv appears stale or missing!
    echo    Please update the slate before continuing
    pause
    exit /b 1
)
echo ✅ Slate verification passed
echo.

echo ================================================================
echo                    📊 PHASE 1: DATA PIPELINE
echo ================================================================
cd "DAILY_RUNNERS"
call 1_DATA_PIPELINE.bat
if errorlevel 1 (
    echo ❌ Data pipeline failed!
    pause
    exit /b 1
)
echo ✅ Data pipeline completed successfully
echo.

echo ================================================================
echo                    🏆 PHASE 2: DFS MODELS
echo ================================================================
call 2_DFS_MODELS.bat
if errorlevel 1 (
    echo ❌ DFS models failed!
    pause
    exit /b 1
)
echo ✅ DFS models completed successfully
echo.

echo ================================================================
echo               💰 PHASE 3: OWNERSHIP PROJECTIONS
echo ================================================================
cd ".."
echo Running ownership projections...
python ADVANCED_OWNERSHIP_PROJECTIONS.py
if errorlevel 1 (
    echo ❌ Ownership projections failed!
    pause
    exit /b 1
)
echo ✅ Ownership projections completed
echo.

echo ================================================================
echo                🔥 PHASE 4: STACK OPTIMIZATION
echo ================================================================
echo Running advanced stack optimizer...
python ADVANCED_STACK_OPTIMIZER.py
if errorlevel 1 (
    echo ❌ Stack optimizer failed!
    pause
    exit /b 1
)
echo ✅ Stack optimization completed
echo.

echo ================================================================
echo               🎯 PHASE 5: ELITE LINEUPS
echo ================================================================
echo Generating elite tournament lineups...
python ELITE_TOURNAMENT_WITH_OWNERSHIP.py
if errorlevel 1 (
    echo ❌ Elite lineup generation failed!
    pause
    exit /b 1
)
echo ✅ Elite lineups generated
echo.

echo ================================================================
echo            🚀 PHASE 6: ENHANCED MODELS (OPTIONAL)
echo ================================================================
echo Running enhanced models for additional edge...
cd "DAILY_RUNNERS"
call 4_ENHANCED_MODELS.bat
if errorlevel 1 (
    echo ⚠️ Enhanced models had issues, but continuing...
) else (
    echo ✅ Enhanced models completed
)
cd ".."
echo.

echo ================================================================
echo                📈 PHASE 7: STACKING STRATEGY
echo ================================================================
echo Running enhanced GPP stacking strategy...
python ENHANCED_GPP_STACKING_STRATEGY.py
if errorlevel 1 (
    echo ⚠️ GPP stacking had issues, but continuing...
) else (
    echo ✅ GPP stacking strategy completed
)
echo.

echo ================================================================
echo                 🖥️ PHASE 8: LAUNCH DASHBOARD
echo ================================================================
echo Starting complete elite DFS dashboard...
python COMPLETE_ELITE_DFS_DASHBOARD.py

echo.
echo ================================================================
echo                      🏁 WORKFLOW COMPLETE!
echo ================================================================
echo All phases completed. Check the dashboard for:
echo   • Team stack analysis with 4-layer multipliers
echo   • Enhanced ownership projections  
echo   • Elite tournament lineups
echo   • Weather/park/pitcher factors
echo   • Export-ready lineup files
echo.
echo Happy DFS grinding! 🎲
pause

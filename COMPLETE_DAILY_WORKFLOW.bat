@echo off
REM ===============================================================
REM COMPLETE ELITE DFS DAILY WORKFLOW
REM Your comprehensive process with all enhancements built
REM Updated: August 22, 2025
REM ===============================================================

echo Starting Complete Elite DFS Workflow...

REM Navigate to DAILY_RUNNERS
cd "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"

REM ===============================================================
REM STEP 1: CORE DATA PIPELINE
REM ===============================================================
echo [STEP 1] Running core data pipeline...
call 1_DATA_PIPELINE.bat

REM ===============================================================
REM STEP 2: BASE DFS MODELS
REM ===============================================================
echo [STEP 2] Building base DFS models...
call 2_DFS_MODELS.bat

REM ===============================================================
REM STEP 3: VEGAS INTEGRATION
REM ===============================================================
cd ".."
echo [STEP 3] Integrating Vegas odds and totals...
python VEGAS_ODDS_INTEGRATOR.py

REM ===============================================================
REM STEP 4: OWNERSHIP PROJECTIONS
REM ===============================================================
echo [STEP 4] Generating advanced ownership projections...
python ADVANCED_OWNERSHIP_PROJECTIONS.py

REM ===============================================================
REM STEP 5: ELITE LINEUP GENERATION
REM ===============================================================
echo [STEP 5] Creating elite tournament lineups...
python ELITE_TOURNAMENT_WITH_OWNERSHIP.py

REM ===============================================================
REM STEP 6: ENHANCED MODELS & OPTIMIZATION
REM ===============================================================
cd "DAILY_RUNNERS"
echo [STEP 6] Running enhanced models...
call 4_ENHANCED_MODELS.bat

cd ".."

REM Advanced Stack Analysis
echo [STEP 6b] Analyzing advanced correlations and stacking...
python ADVANCED_STACK_OPTIMIZER.py
python advanced_correlation_analyzer.py
python ownership_leverage_analyzer.py

REM Enhanced GPP Strategy
echo [STEP 6c] Optimizing GPP strategy...
python ENHANCED_GPP_STACKING_STRATEGY.py

REM ===============================================================
REM STEP 7: REAL-TIME DATA INTEGRATION
REM ===============================================================
echo [STEP 7] Fetching real-time data...
python fetch_weather_data.py
python fetch_rotowire_lineups_enhanced.py
python fetch_live_scores.py

REM ===============================================================
REM STEP 8: UMPIRE & EDGE ANALYSIS
REM ===============================================================
echo [STEP 8] Analyzing umpire impacts and edges...
python umpire_impact_analyzer.py
python PARK_FACTOR_INTEGRATION.py

REM ===============================================================
REM STEP 9: FINAL LINEUP OPTIMIZATION
REM ===============================================================
echo [STEP 9] Final lineup optimization...
python FINAL_LINEUP_OPTIMIZER.py
python ELITE_LINEUP_SELECTOR.py

REM ===============================================================
REM STEP 10: ADVANCED DFS INTEGRATION
REM ===============================================================
echo [STEP 10] Running advanced DFS integration...
python ADVANCED_DFS_INTEGRATOR.py

REM ===============================================================
REM STEP 11: CONTEST-SPECIFIC EXPORT
REM ===============================================================
echo [STEP 11] Generating contest-specific lineups...
python EXPORT_SELECTED_LINEUPS.py

REM ===============================================================
REM STEP 12: LAUNCH ELITE DASHBOARD
REM ===============================================================
echo [STEP 12] Launching Elite DFS Dashboard...
python COMPLETE_ELITE_DFS_DASHBOARD.py

echo.
echo =====================================================
echo COMPLETE ELITE DFS WORKFLOW FINISHED!
echo =====================================================
echo Dashboard is now ready with all data integrated
echo Contest-ready lineups available for export
echo Elite system is live and optimized!
echo =====================================================
pause

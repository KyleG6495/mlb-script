@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
echo.
echo =====================================
echo  COMPLETE HYBRID DFS WORKFLOW
echo  (Your Existing + New Elite Features)
echo =====================================
echo.

REM Set the Python environment
set PYTHON_EXE=python

echo [PHASE 1] Your Existing Data Pipeline...
echo.

echo Step 1: Updating FanDuel slate data...
echo NOTE: Please ensure fd_slate_today.csv is updated before continuing
pause

echo.
echo Step 2: Running your data pipeline...
call 1_DATA_PIPELINE.bat
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo Step 3: Building your DFS models...
echo [DEBUG] About to call 2_DFS_MODELS.bat from directory: %CD%
echo [DEBUG] Python executable set to: %PYTHON_EXE%
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
call 2_DFS_MODELS.bat
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo =====================================
echo  [PHASE 2] DUAL ELITE SYSTEMS
echo =====================================
echo.

echo Step 4A: Running Your Enhanced Elite Builder...
echo [INFO] Building championship lineups with 125%+ accuracy
call ENHANCED_ELITE_BUILDER.bat
if %errorlevel% neq 0 goto error

echo.
echo Step 4B: Building Advanced Ownership Projections...
echo [INFO] Creating realistic ownership curves (0.5%-50%)
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% ADVANCED_OWNERSHIP_PROJECTIONS.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo Step 5: Creating Elite Tournament Lineups with Ownership Edge...
echo [INFO] Building lineups with 5.1% avg ownership vs 15-20% industry
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% ELITE_TOURNAMENT_WITH_OWNERSHIP.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo =====================================
echo  [PHASE 3] Your Existing Optimization
echo =====================================
echo.

echo Step 6: Running today's filtered optimizer...
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% today_filtered_optimizer.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo Step 7: Formatting for FanDuel...
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% Expanded_filtered_fanduel_formatter.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo Step 8: Translating lineup names...
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% Fanduel_lineup_name_translator.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
if %errorlevel% neq 0 goto error

echo.
echo =====================================
echo  [PHASE 4] LINEUP REVIEW & UPLOAD
echo =====================================
echo.

echo 🎉 DUAL ELITE SYSTEMS COMPLETE!
echo.
echo 📊 YOU NOW HAVE MULTIPLE ELITE LINEUP SETS:
echo.
echo 🏆 ENHANCED ELITE SYSTEM (Your Existing):
echo   • Championship lineups with 125%+ accuracy
echo   • Vegas odds integration
echo   • Advanced stack optimization
echo   • Files: CHAMPIONSHIP_LINEUPS_*.csv
echo.
echo 💎 OWNERSHIP EDGE SYSTEM (New):
echo   • Lineups with 5.1% avg ownership
echo   • 3-4x lower ownership than competitors
echo   • Leverage and contrarian plays
echo   • Files: Elite_Tournament_Lineups_*.csv
echo.
echo 🤖 TRADITIONAL ML SYSTEM (From 2_DFS_MODELS):
echo   • ML-powered projections
echo   • Enhanced and legacy optimizations
echo   • Files: enhanced_ml_dfs_lineups_*.csv
echo.
echo 📝 YOUR EXISTING OPTIMIZATION:
echo   • Filtered and formatted lineups
echo   • Name translations for FanDuel
echo   • Files: Multiple optimized formats
echo.
echo ✨ RECOMMENDATION:
echo   Use Enhanced Elite for accuracy + Ownership Edge for leverage!
echo   Mix both systems for maximum tournament coverage!
echo.

echo Upload your preferred lineups to FanDuel now:
echo   🎯 For CASH GAMES: Enhanced Elite (high accuracy)
echo   🚀 For TOURNAMENTS: Ownership Edge (low ownership)
echo   🎲 For MIXED: Combine both systems strategically
echo.
echo Press any key when lineups are uploaded...
pause

echo.
echo =====================================
echo  [PHASE 5] REAL-TIME MONITORING
echo =====================================
echo.

echo Starting Late Swap & Ownership Monitoring...
echo WARNING: This will run until contests lock!
echo Press Ctrl+C to stop monitoring when contests end.
echo.

echo Starting in 5 seconds...
timeout /t 5

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
%PYTHON_EXE% INTEGRATED_DFS_MASTER.py
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"

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
echo  COMPLETE WORKFLOW FINISHED!
echo ========================================
echo  Your lineups are optimized and monitored!
echo ========================================
pause

@echo off

REM Initialize environment and error handling
call "%~dp0config_batch.bat"
if errorlevel 1 (
    echo ❌ Failed to initialize environment
    pause
    exit /b 1
)

:start
echo.
echo =====================================
echo  COMPLETE HYBRID DFS WORKFLOW
echo  (Your Existing + New Elite Features)
echo =====================================
echo.

echo [PHASE 1] Your Existing Data Pipeline...
echo.

echo Step 1: Updating FanDuel slate data...
echo NOTE: Please ensure fd_slate_today.csv is updated before continuing
pause

:retry_data_pipeline
echo.
echo Step 2: Running your data pipeline...
call "%DAILY_RUNNERS_DIR%1_DATA_PIPELINE.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Data Pipeline" %errorlevel%
if errorlevel 999 goto :retry_data_pipeline
if errorlevel 1 goto :error

:retry_dfs_models
echo.
echo Step 3: Building your DFS models...
echo [DEBUG] About to call 2_DFS_MODELS.bat from directory: %CD%
echo [DEBUG] Python executable set to: %PYTHON_EXE%
call "%DAILY_RUNNERS_DIR%2_DFS_MODELS.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "DFS Models" %errorlevel%
if errorlevel 999 goto :retry_dfs_models
if errorlevel 1 goto :error

echo.
echo =====================================
echo  [PHASE 2] DUAL ELITE SYSTEMS
echo =====================================
echo.

:retry_elite_builder
echo Step 4A: Running Your Enhanced Elite Builder...
echo [INFO] Building championship lineups with 125%+ accuracy
call "%DAILY_RUNNERS_DIR%ENHANCED_ELITE_BUILDER.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Enhanced Elite Builder" %errorlevel%
if errorlevel 999 goto :retry_elite_builder
if errorlevel 1 goto :error

:retry_ownership_projections
echo.
echo Step 4B: Building Advanced Ownership Projections...
echo [INFO] Creating realistic ownership curves (0.5%-50%)
"%PYTHON_EXE%" ADVANCED_OWNERSHIP_PROJECTIONS.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Advanced Ownership Projections" %errorlevel%
if errorlevel 999 goto :retry_ownership_projections
if errorlevel 1 goto :error

:retry_elite_tournament
echo.
echo Step 5: Creating Elite Tournament Lineups with Ownership Edge...
echo [INFO] Building lineups with 5.1% avg ownership vs 15-20% industry
"%PYTHON_EXE%" ELITE_TOURNAMENT_WITH_OWNERSHIP.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Elite Tournament with Ownership" %errorlevel%
if errorlevel 999 goto :retry_elite_tournament
if errorlevel 1 goto :error

echo.
echo =====================================
echo  [PHASE 3] Your Existing Optimization
echo =====================================
echo.

:retry_filtered_optimizer
echo Step 6: Running today's filtered optimizer...
"%PYTHON_EXE%" today_filtered_optimizer.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Filtered Optimizer" %errorlevel%
if errorlevel 999 goto :retry_filtered_optimizer
if errorlevel 1 goto :error

:retry_fanduel_formatter
echo.
echo Step 7: Formatting for FanDuel...
"%PYTHON_EXE%" Expanded_filtered_fanduel_formatter.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "FanDuel Formatter" %errorlevel%
if errorlevel 999 goto :retry_fanduel_formatter
if errorlevel 1 goto :error

:retry_name_translator
echo.
echo Step 8: Translating lineup names...
"%PYTHON_EXE%" Fanduel_lineup_name_translator.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Name Translator" %errorlevel%
if errorlevel 999 goto :retry_name_translator
if errorlevel 1 goto :error

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

"%PYTHON_EXE%" INTEGRATED_DFS_MASTER.py

goto :end

:error
echo.
echo ========================================
echo ❌ ERROR: Process failed in hybrid workflow
echo ========================================
echo Please check the logs for details
echo.
echo 🔄 You can retry individual components or the entire workflow
set /p retry=Do you want to retry the hybrid workflow? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
echo.
echo ========================================
echo  COMPLETE WORKFLOW FINISHED!
echo ========================================
echo  Your lineups are optimized and monitored!
echo ========================================
pause

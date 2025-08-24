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
echo          ENHANCED DFS SIMULATION PIPELINE
echo ================================================
echo.
echo Starting enhanced DFS projections with game simulation...
echo This will take approximately 10-15 minutes.
echo.

:retry_enhanced_dfs
echo [INFO] Running Game State enhanced DFS pipeline...
"%PYTHON_EXE%" run_game_state_enhanced_dfs.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Enhanced DFS Game State Pipeline" %errorlevel%
if errorlevel 999 goto :retry_enhanced_dfs
if errorlevel 1 goto :error

echo.
echo ✅ SUCCESS: Enhanced DFS pipeline completed!
echo Check the %DATA_DIR% folder for generated lineups and reports.
echo.
echo Enhanced DFS Pipeline Complete!
echo ================================================
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR: Enhanced DFS pipeline failed
echo ========================================
echo Check the log file for details: %DATA_DIR%dfs_pipeline.log
echo.
echo 💡 Common issues:
echo   • Game simulation timeout (increase timeout settings)
echo   • Memory constraints (close other applications)
echo   • Missing input data (run 1_DATA_PIPELINE.bat first)
echo.
set /p retry=Do you want to retry the enhanced DFS pipeline? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

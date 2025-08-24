@echo off
REM 🚀 COMPLETE DAILY MLB WORKFLOW 🚀
REM This runs the entire daily pipeline in the correct order

REM Initialize environment and error handling
call "%~dp0config_batch.bat"
if errorlevel 1 (
    echo ❌ Failed to initialize environment
    pause
    exit /b 1
)

:start
echo.
echo ================================================================
echo 🏆 STARTING COMPLETE DAILY MLB WORKFLOW 🏆
echo Date: %date% %time%
echo ================================================================
echo.

:retry_validation
REM Step 1: Validate current data state
echo 🔍 STEP 1: Validating current data state...
"%PYTHON_EXE%" DAILY_DATA_VALIDATOR.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Data Validation" %errorlevel%
if errorlevel 999 goto :retry_validation
if errorlevel 1 goto :error
echo ✅ Data validation complete
echo.

:retry_data_pipeline
REM Step 2: Run data pipeline
echo 📊 STEP 2: Running data collection pipeline...
call "%DAILY_RUNNERS_DIR%1_DATA_PIPELINE.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Data Collection Pipeline" %errorlevel%
if errorlevel 999 goto :retry_data_pipeline
if errorlevel 1 goto :error
echo ✅ Data collection complete
echo.

:retry_dfs_models
REM Step 3: Run DFS optimization
echo 🎯 STEP 3: Running DFS optimization...
call "%DAILY_RUNNERS_DIR%2_DFS_MODELS.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "DFS Optimization" %errorlevel%
if errorlevel 999 goto :retry_dfs_models
if errorlevel 1 goto :error
echo ✅ DFS optimization complete
echo.

:retry_enhanced_dfs
REM Step 4: Enhanced DFS with validation
echo 🔧 STEP 4: Running enhanced DFS optimization...
call "%DAILY_RUNNERS_DIR%2B_ENHANCED_DFS.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Enhanced DFS Optimization" %errorlevel%
if errorlevel 999 goto :retry_enhanced_dfs
if errorlevel 1 goto :error
echo ✅ Enhanced DFS optimization complete
echo.

:retry_prop_models
REM Step 5: Run prop models
echo 🎲 STEP 5: Running prop prediction models...
call "%DAILY_RUNNERS_DIR%3_PROP_MODELS.bat"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Prop Prediction Models" %errorlevel%
if errorlevel 999 goto :retry_prop_models
if errorlevel 1 goto :error
echo ✅ Prop models complete
echo.

:retry_stack_optimizer
REM Step 6: Run stack optimization
echo 📚 STEP 6: Running stack optimization...
"%PYTHON_EXE%" ADVANCED_STACK_OPTIMIZER.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Stack Optimization" %errorlevel%
if errorlevel 999 goto :retry_stack_optimizer
if errorlevel 1 goto :error
echo ✅ Stack optimization complete
echo.

:retry_final_validation
REM Step 7: Final validation
echo 🔍 STEP 7: Running final validation...
"%PYTHON_EXE%" DAILY_DATA_VALIDATOR.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Final Validation" %errorlevel%
if errorlevel 999 goto :retry_final_validation
if errorlevel 1 goto :error
echo ✅ Final validation complete
echo.

:retry_dashboard
REM Step 8: Launch dashboard
echo 🌐 STEP 8: Launching dashboard...
echo Starting real_data_dashboard.py in background...
start "MLB Dashboard" "%PYTHON_EXE%" real_data_dashboard.py
if errorlevel 1 (
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Dashboard Launch" %errorlevel%
    if errorlevel 999 goto :retry_dashboard
    if errorlevel 1 goto :error
)
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
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR in daily workflow!
echo ========================================
echo Check the output above for details.
echo.
echo 💡 Common issues and solutions:
echo   • API rate limits → Wait and retry individual steps
echo   • Network connectivity → Check internet connection
echo   • Missing input files → Verify data pipeline completion
echo   • Dashboard conflicts → Close existing dashboards
echo.
echo 🔄 You can retry individual components:
echo   • Data Pipeline: 1_DATA_PIPELINE.bat
echo   • DFS Models: 2_DFS_MODELS.bat
echo   • Prop Models: 3_PROP_MODELS.bat
echo.
set /p retry=Do you want to retry the entire workflow? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

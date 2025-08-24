@echo off

REM Initialize environment and error handling
call "%~dp0config_batch.bat"
if errorlevel 1 (
    echo ❌ Failed to initialize environment
    pause
    exit /b 1
)

:start
echo ===============================================
echo 🚀 COMPLETE OPTIMIZATION WORKFLOW
echo 🎯 Simulations + Ownership + Advanced Lineups
echo ===============================================
echo.

:retry_ultimate_optimizer
echo 📊 STEP 1: Running Ultimate Optimization Engine...
echo ⚡ This includes: 2000 simulations per player, ownership projections, correlations
"%PYTHON_EXE%" ULTIMATE_CONFIRMED_OPTIMIZER.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Ultimate Optimization Engine" %errorlevel%
if errorlevel 999 goto :retry_ultimate_optimizer
if errorlevel 1 goto :error

:retry_advanced_constructor
echo.
echo 🏆 STEP 2: Constructing Advanced Lineups...
echo 🎭 Multiple strategies: Balanced, Ceiling, Leverage, Cash
"%PYTHON_EXE%" ADVANCED_LINEUP_CONSTRUCTOR.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Advanced Lineup Constructor" %errorlevel%
if errorlevel 999 goto :retry_advanced_constructor
if errorlevel 1 goto :error

echo.
echo ===============================================
echo ✅ COMPLETE OPTIMIZATION WORKFLOW FINISHED!
echo 📈 Optimized projections created
echo 🏆 Advanced lineups generated  
echo 🎯 Ready for submission!
echo ===============================================
echo.

echo 📋 Generated files:
echo    📊 confirmed_optimized_projections.csv
echo    🏆 OPTIMIZED_LINEUPS_[timestamp].csv
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR in optimization workflow!
echo ========================================
echo.
echo 💡 Common issues:
echo   • Memory constraints for 2000 simulations per player
echo   • Missing confirmed starters data
echo   • Ownership data unavailable
echo   • Correlation calculation timeout
echo.
set /p retry=Do you want to retry the optimization workflow? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

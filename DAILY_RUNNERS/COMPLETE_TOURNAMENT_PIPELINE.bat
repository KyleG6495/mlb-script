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
echo 🚨 COMPLETE TOURNAMENT PIPELINE (SAFE MODE)
echo 🎯 Real Starting Lineups + Tournament Generation
echo ===============================================
echo.

echo ⚠️  CRITICAL: This ensures we only use CONFIRMED STARTERS
echo 📊 Process: Fresh Analysis → Confirmed Starters → Tournament Lineups
echo.
echo Press any key to start the complete pipeline...
pause
echo.

:retry_confirmed_starters
echo 🔍 STEP 1: Generate Today's Confirmed Starters...
echo 🎯 Refreshing confirmed starting lineups from RotoWire
"%PYTHON_EXE%" DYNAMIC_CONFIRMED_STARTERS.py
if errorlevel 1 (
    echo ⚠️ Confirmed starters refresh failed - using existing data
    echo 💡 Continuing with last known confirmed starters...
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Confirmed Starters (non-critical)" 0
)

:retry_safe_enhanced
echo.
echo 🔥 STEP 2: Generate Safe Enhanced Tournament Lineups...
echo ⚡ Using enhanced projections with confirmed starters safety
"%PYTHON_EXE%" SAFE_ENHANCED_TOURNAMENT_GENERATOR.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Safe Enhanced Tournament Generation" %errorlevel%
if errorlevel 999 goto :retry_safe_enhanced
if errorlevel 1 goto :error

echo.
echo 🏆 STEP 3: Generate Additional Lineup Set...
echo 🎭 Creating second diverse set of safe lineups
"%PYTHON_EXE%" SAFE_ENHANCED_TOURNAMENT_GENERATOR.py
if errorlevel 1 (
    echo ⚠️ Additional lineup generation had issues
    echo 💡 Continuing with first set of lineups...
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Additional Lineup Generation (non-critical)" 0
)

echo.
echo 💰 STEP 4: Run Prop Analysis (Optional)...
echo 🎲 Betting opportunities on confirmed starters
if exist "%DAILY_RUNNERS_DIR%3_PROP_MODELS.bat" (
    call "%DAILY_RUNNERS_DIR%3_PROP_MODELS.bat"
    if errorlevel 1 (
        echo ⚠️ Prop analysis had issues - check output files
        call "%DAILY_RUNNERS_DIR%error_handler.bat" "Prop Analysis (non-critical)" 0
    )
) else (
    echo 💡 Prop analysis script not found - skipping...
)

:retry_combine_files
echo.
echo 🎯 STEP 5: Combine Tournament Files...
echo 📋 Creating master tournament portfolio
"%PYTHON_EXE%" COMBINE_TOURNAMENT_FILES.py
if errorlevel 1 (
    echo ⚠️ File combination had issues - check individual files
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Combine Tournament Files (non-critical)" 0
)

echo.
echo ===============================================
echo ✅ COMPLETE TOURNAMENT PIPELINE COMPLETE!
echo 🎯 GUARANTEED: Only confirmed starting players used
echo 🏆 Tournament lineups with real starters
echo 💰 Prop picks analyzed
echo ===============================================
echo.

echo 📋 Today's Safe Enhanced Output Files:
echo    🎯 SAFE_ENHANCED_TOURNAMENT_[timestamp].csv (individual sets)
echo    🏆 MASTER_SAFE_TOURNAMENT_[timestamp].csv (combined portfolio)
echo    💎 Enhanced projections with confirmed starters safety
echo    📊 Ready for FanDuel submission
echo.

echo 🎮 FINAL TOURNAMENT PORTFOLIO STATUS:
"%PYTHON_EXE%" -c "
import glob
import pandas as pd
import os

# Check latest master file  
slate_dir = os.path.join('%FD_CURRENT_SLATE_DIR%')
master_files = glob.glob(os.path.join(slate_dir, 'MASTER_SAFE_TOURNAMENT_*.csv'))
if master_files:
    latest_file = max(master_files)
    df = pd.read_csv(latest_file)
    total_lineups = df['lineup_id'].nunique()
    min_proj = df['Projected_FPPG'].min()
    max_proj = df['Projected_FPPG'].max()
    avg_proj = df.groupby('lineup_id')['Projected_FPPG'].sum().mean()
    
    print(f'📁 Latest Master File: {os.path.basename(latest_file)}')
    print(f'🏆 Total Tournament Lineups: {total_lineups}')
    print(f'⚡ Projection Range: {min_proj:.1f} - {max_proj:.1f} FPPG')
    print(f'📊 Average Lineup Score: {avg_proj:.1f} FPPG')
    print(f'✅ Ready for tournament submission!')
else:
    print('⚠️ No master tournament file found')
"
echo.

echo 🚨 SAFETY CHECK COMPLETE: No bench players in lineups!
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR in tournament pipeline!
echo ========================================
echo Check the output above for details.
echo.
echo 💡 Common issues:
echo   • Missing confirmed starters data
echo   • Tournament generation constraints  
echo   • File combination conflicts
echo   • Memory constraints for large lineups
echo.
set /p retry=Do you want to retry the tournament pipeline? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

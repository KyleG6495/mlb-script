@echo off
echo [DEBUG] 2_DFS_MODELS.bat starting...
echo [DEBUG] Current directory: %CD%
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo [DEBUG] Changed to Scripts directory: %CD%

REM Use PYTHON_EXE if set, otherwise default to python
if "%PYTHON_EXE%"=="" set PYTHON_EXE=python
echo [DEBUG] Python executable: %PYTHON_EXE%

echo ========================================
echo   🏆 DFS AND FANTASY LINEUP OPTIMIZATION
echo   Model-Based Lineup Generation
echo ========================================
echo.
echo Current directory: %CD%
echo This runs ML models to optimize FanDuel lineups
echo Total time: ~8-12 minutes
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (1_DATA_PIPELINE.bat)
echo   ✅ fd_slate_today.csv updated with today's slate
echo   ✅ starting_lineups.csv created (confirmed starters only)
echo.
echo Checking for starting lineups master file...
if exist "../data/starting_lineups.csv" (
    echo ✅ Starting lineups master file found - using confirmed starters only
    echo [DEBUG] Attempting to run Python with: %PYTHON_EXE%
    %PYTHON_EXE% --version
    if errorlevel 1 (
        echo [ERROR] Python executable not found: %PYTHON_EXE%
        echo [INFO] Trying alternative Python paths...
        where python
        where python3
        echo [INFO] Please ensure Python is installed and in PATH
        pause
        exit /b 1
    )
    %PYTHON_EXE% -c "import pandas as pd; df=pd.read_csv('../data/starting_lineups.csv'); print(f'📊 Using {len(df)} confirmed starters from master file')"
) else (
    echo ❌ starting_lineups.csv not found!
    echo Please run create_starting_lineups.py first
    pause
    exit /b 1
)
echo.
echo Checking batting order availability...
echo [DEBUG] Attempting to run: %PYTHON_EXE% check_batting_orders.py
if exist "check_batting_orders.py" (
    %PYTHON_EXE% check_batting_orders.py
    if errorlevel 1 (
        echo.
        echo ⚠️ BATTING ORDERS NOT AVAILABLE YET
        echo This will use backup quintuple lineup optimization
        echo For full ML optimization, run this script later when batting orders are posted
        echo.
    ) else (
        echo ✅ Batting orders confirmed and available
    )
) else (
    echo [WARNING] check_batting_orders.py not found, skipping batting order check
)
    echo ✅ Batting orders available - full ML optimization will run
    echo.
)
echo Press any key to start lineup optimization...
pause
echo.

echo Step 1: Finalizing Hitter Features...
%PYTHON_EXE% "(21)finalize_hitter_features.py"
if errorlevel 1 goto error

echo Step 2: Finalizing Pitcher Features...
%PYTHON_EXE% "(22)finalize_pitcher_features.py"
if errorlevel 1 goto error

echo Step 3: Adding Pitcher Context...
%PYTHON_EXE% add_pitcher_features.py
if errorlevel 1 goto error

echo Step 4: Applying Real Player Stats...
%PYTHON_EXE% fix_prediction_features_with_real_stats.py
if errorlevel 1 goto error

echo Step 5: Running Enhanced ML-Powered DFS Optimization...
%PYTHON_EXE% ENHANCED_ML_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Enhanced ML DFS failed - likely batting orders not posted yet
    echo Running backup quintuple lineup generator...
    %PYTHON_EXE% generate_quintuple_lineups.py
    if errorlevel 1 goto error
    echo ✅ Generated backup quintuple lineups successfully
    goto skip_legacy_dfs
)

echo Step 6: Running ML-Powered DFS Optimization (legacy)...
%PYTHON_EXE% ML_POWERED_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Legacy ML DFS also failed - using quintuple backup
    goto skip_legacy_dfs
)

echo Step 7: Running Unified DFS Optimization (comparison)...
%PYTHON_EXE% UNIFIED_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Unified DFS also failed - batting orders likely not available
)

:skip_legacy_dfs

echo Step 8: Creating Additional Lineup Formats...
%PYTHON_EXE% "24. create_fanduel_submission.py"
if errorlevel 1 goto error

echo Step 9: Generating Quintuple Tournament Lineups...
%PYTHON_EXE% generate_quintuple_lineups.py
if errorlevel 1 (
    echo ⚠️ Quintuple lineup generation failed, continuing...
) else (
    echo ✅ Quintuple tournament lineups generated successfully
)

echo.
echo ========================================
echo 🎉 DFS OPTIMIZATION COMPLETE! 
echo ========================================
echo.
echo 🎯 LINEUP FILES CREATED:
echo   🚀 enhanced_ml_dfs_lineups_*.csv (ENHANCED ML - if batting orders available)
echo   🏆 ranked_lineups_*.csv (detailed analysis & rankings)
echo   🎯 fanduel_submission_*.csv (ready to upload)
echo   🤖 ml_dfs_lineups_*.csv (legacy ML-powered lineups)
echo   📊 unified_dfs_lineups_*.csv (traditional optimization)
echo   📋 unified_dfs_summary_*.csv (lineup overview)
echo   📝 fanduel_submission_names.csv (alternate format)
echo   🎯 quintuple_lineups_combined_*.csv (TOURNAMENT SPECIFIC - 200 player events!)
echo   🎲 quintuple_lineup_1_balanced_*.csv (individual lineup files)
echo   🎲 quintuple_lineup_2_contrarian_*.csv (individual lineup files)
echo.
echo 💡 BATTING ORDER STATUS:
echo   ⏰ If batting orders aren't posted yet, quintuple lineups were generated
echo   ✅ Quintuple lineups work without batting orders (salary-based optimization)
echo   🔄 Re-run this script later when batting orders are available for full ML optimization
echo.
echo 🏆 ENHANCED LINEUP BREAKDOWN:
echo   💰 5 CASH GAME lineups (high floor, safe plays)
echo   🎯 8 SMALL TOURNAMENT lineups (balanced risk/reward)
echo   🚀 7 LARGE GPP lineups (high ceiling, tournament winners)
echo   📊 All lineups ranked by contest-specific criteria
echo   🔄 TRUE diversity (no duplicate lineups!)
echo.
echo 💰 VALIDATION CHECKS:
echo   ✅ $35,000 salary cap enforced
echo   ✅ 9 players per lineup (P+C+1B+2B+3B+SS+3OF)
echo   🤖 ML projections using trained prop models
echo   📊 Enhanced projections with weather/matchups
echo   ✅ Lineup diversity (no duplicates)
echo.
echo 🚀 READY FOR FANDUEL SUBMISSION!
echo   BEST: enhanced_ml_dfs_lineups_*.csv (contest-optimized + diverse)
echo   Analysis: ranked_lineups_*.csv (see top performers by contest type)
echo   Upload: fanduel_submission_*.csv (top lineups formatted for FD)
echo   Legacy: ml_dfs_lineups_*.csv (original ML system)
echo.
echo 💡 ENHANCED STRATEGY GUIDE:
echo   • Cash games → Use TOP 3 CASH lineups from rankings
echo   • Small tournaments → Use TOP 3 SMALL_TOURNAMENT lineups  
echo   • Large GPPs → Use TOP 3 LARGE_GPP lineups
echo   • All lineups are DIVERSE and optimized for specific contests!
echo.
echo 🤖 NEW: ML-POWERED PROJECTIONS!
echo   Your DFS system now uses the SAME advanced models as prop betting:
echo   ✅ XGBoost ensemble predictions
echo   ✅ Hits, HR, RBI, Runs converted to fantasy points
echo   ✅ Pitcher strikeouts, wins, innings predictions
echo   ✅ Much more accurate than salary-based estimates
echo.
echo 🚀 NEXT STEP: Run 3_PROP_MODELS.bat for betting analysis
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in DFS optimization!
echo Check the output above for details.
echo.
echo Troubleshooting checklist:
echo   ❓ Did you run 1_DATA_PIPELINE.bat first?
echo   ❓ Is fd_slate_today.csv updated with today's slate?
echo   ❓ Are fd_hitter_features_final.csv and fd_pitcher_features_final.csv present?
echo   ❓ Do you have players available in all positions?
echo.
echo Required files:
echo   📄 data/fd_slate_today.csv
echo   📄 data/fd_hitter_features_final.csv  
echo   📄 data/fd_pitcher_features_final.csv
echo.

:end
pause

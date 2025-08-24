@echo off
REM ============================================================================
REM 📊 MLB DATA PIPELINE - Standardized Data Collection
REM Steps 1-20: Fresh Data Collection (~35-45 minutes)  
REM ============================================================================

REM Initialize standardized environment
call "%~dp0config_batch.bat"

echo ========================================
echo   📊 MLB DATA PIPELINE - PULL & SCRAPE
echo   Steps 1-20: Fresh Data Collection
echo ========================================
echo.
echo Current directory: %CD%
echo This pulls all fresh data from APIs and websites
echo Total time: ~35-45 minutes
echo.
echo Press any key to start data collection...
pause
echo.

:retry_rotowire
echo Step 0.5: Fetching Rotowire Confirmed Lineups (Enhanced - 100%% Coverage)...
"%PYTHON_EXE%" fetch_rotowire_lineups_enhanced.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Enhanced Rotowire Fetch" %errorlevel%
if errorlevel 999 goto :retry_rotowire
if errorlevel 1 (
    echo ⚠️ Enhanced Rotowire fetch failed - trying fallback...
    "%PYTHON_EXE%" fetch_rotowire_lineups.py
    call "%DAILY_RUNNERS_DIR%error_handler.bat" "Fallback Rotowire Fetch" %errorlevel%
    if errorlevel 1 (
        echo ⚠️ Rotowire fetch failed completely - continuing with FD data only
    ) else (
        echo ✅ Rotowire data fetched successfully (75%% coverage fallback)
    )
) else (
    echo ✅ Enhanced Rotowire data fetched successfully (100%% coverage)
)

:retry_lineups
echo Step 1.5: Creating Starting Lineups Master File...
"%PYTHON_EXE%" create_starting_lineups.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Create Starting Lineups" %errorlevel%
if errorlevel 999 goto :retry_lineups
if errorlevel 1 goto :error
echo ✅ Starting lineups master file created

:retry_pipeline_ready
echo Step 1.6: Creating Pipeline-Ready Starters File...
"%PYTHON_EXE%" create_pipeline_ready_starters.py
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Create Pipeline-Ready Starters" %errorlevel%
if errorlevel 999 goto :retry_pipeline_ready
if errorlevel 1 goto :error
echo ✅ Pipeline-ready starters file created - data pipeline will use ONLY confirmed starters

:retry_hitter_games
echo Step 1: Generating Hitter Games (Confirmed Starters Only)...
"%PYTHON_EXE%" "(1)generate_hitter_games.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Generate Hitter Games" %errorlevel%
if errorlevel 999 goto :retry_hitter_games
if errorlevel 1 goto :error

:retry_hitter_ids
echo Step 2: Assigning Hitter IDs...
"%PYTHON_EXE%" "(2)assign_hitter_ids.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Assign Hitter IDs" %errorlevel%
if errorlevel 999 goto :retry_hitter_ids
if errorlevel 1 goto :error

:retry_hitter_pk
echo Step 3: Assigning Hitter Game PKs...
"%PYTHON_EXE%" "(3)assign_hitter_game_pk.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Assign Hitter Game PKs" %errorlevel%
if errorlevel 999 goto :retry_hitter_pk
if errorlevel 1 goto :error

:retry_pitcher_games
echo Step 4: Generating Pitcher Games...
"%PYTHON_EXE%" "(2)generate_pitcher_games.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Generate Pitcher Games" %errorlevel%
if errorlevel 999 goto :retry_pitcher_games
if errorlevel 1 goto :error

:retry_pitcher_ids
echo Step 5: Assigning Pitcher IDs...
"%PYTHON_EXE%" "5. assign_player_ids.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Assign Pitcher IDs" %errorlevel%
if errorlevel 999 goto :retry_pitcher_ids
if errorlevel 1 goto :error

:retry_pitcher_pk
echo Step 6: Assigning Pitcher Game PKs...
"%PYTHON_EXE%" "(3) assign_pitcher_game_pk.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Assign Pitcher Game PKs" %errorlevel%
if errorlevel 999 goto :retry_pitcher_pk
if errorlevel 1 goto :error

:retry_hitter_stats
echo Step 7: Scraping Hitter Stats...
"%PYTHON_EXE%" "(5)scrape_hitter_stats.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Scrape Hitter Stats" %errorlevel%
if errorlevel 999 goto :retry_hitter_stats
if errorlevel 1 goto :error

:retry_pitcher_stats
echo Step 8: Scraping Pitcher Stats...
"%PYTHON_EXE%" "(6)scrape_pitcher_stats.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Scrape Pitcher Stats" %errorlevel%
if errorlevel 999 goto :retry_pitcher_stats
if errorlevel 1 goto :error

:retry_earned_runs
echo Step 9: Fetching Earned Runs...
"%PYTHON_EXE%" "(9)fetch_earned_runs.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Fetch Earned Runs" %errorlevel%
if errorlevel 999 goto :retry_earned_runs
if errorlevel 1 goto :error

:retry_aggregate_pitcher
echo Step 10: Aggregating Pitcher Stats...
"%PYTHON_EXE%" "(11)aggregate_pitcher_stats.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Aggregate Pitcher Stats" %errorlevel%
if errorlevel 999 goto :retry_aggregate_pitcher
if errorlevel 1 goto :error

:retry_today_pitcher
echo Step 11: Building Today Pitcher Features...
"%PYTHON_EXE%" "(8)build_today_pitcher_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Build Today Pitcher Features" %errorlevel%
if errorlevel 999 goto :retry_today_pitcher
if errorlevel 1 goto :error

:retry_rolling_hitter
echo Step 12: Building Rolling Hitter Features...
"%PYTHON_EXE%" "(12)build_rolling_hitter_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Build Rolling Hitter Features" %errorlevel%
if errorlevel 999 goto :retry_rolling_hitter
if errorlevel 1 goto :error

:retry_rolling_pitcher
echo Step 13: Building Rolling Pitcher Features...
"%PYTHON_EXE%" "(13)build_rolling_pitcher_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Build Rolling Pitcher Features" %errorlevel%
if errorlevel 999 goto :retry_rolling_pitcher
if errorlevel 1 goto :error

:retry_today_hitter
echo Step 14: Building Today Hitter Features...
"%PYTHON_EXE%" "(7)build_today_hitter_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Build Today Hitter Features" %errorlevel%
if errorlevel 999 goto :retry_today_hitter
if errorlevel 1 goto :error

:retry_merge_hitter
echo Step 15: Merging Hitter Features...
"%PYTHON_EXE%" "(6)merge_hitter_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Merge Hitter Features" %errorlevel%
if errorlevel 999 goto :retry_merge_hitter
if errorlevel 1 goto :error

:retry_merge_pitcher
echo Step 16: Merging Pitcher Features...
"%PYTHON_EXE%" "(15)merge_pitcher_features.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Merge Pitcher Features" %errorlevel%
if errorlevel 999 goto :retry_merge_pitcher
if errorlevel 1 goto :error

:retry_hitter_team_map
echo Step 17: Generating Hitter Team Map...
"%PYTHON_EXE%" "(18)generate_hitter_team_map.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Generate Hitter Team Map" %errorlevel%
if errorlevel 999 goto :retry_hitter_team_map
if errorlevel 1 goto :error

:retry_pitcher_team_map
echo Step 18: Generating Pitcher Team Map...
"%PYTHON_EXE%" "(18)generate_pitcher_team_map.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Generate Pitcher Team Map" %errorlevel%
if errorlevel 999 goto :retry_pitcher_team_map
if errorlevel 1 goto :error

:retry_weather
echo Step 19: Building Weather Data...
"%PYTHON_EXE%" "(19)build_weather_today.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Build Weather Data" %errorlevel%
if errorlevel 999 goto :retry_weather
if errorlevel 1 goto :error

:retry_weather_park
echo Step 20: Merging Weather and Park Factors...
"%PYTHON_EXE%" "(20))merge_weather_and_park_factors.py"
call "%DAILY_RUNNERS_DIR%error_handler.bat" "Merge Weather and Park Factors" %errorlevel%
if errorlevel 999 goto :retry_weather_park
if errorlevel 1 goto :error

echo.
echo ========================================
echo 🎉 DATA PIPELINE COMPLETE! 
echo ========================================
echo.
echo ✅ Fresh data collected for:
echo   📊 Hitter stats and features
echo   ⚾ Pitcher stats and features  
echo   🌤️ Weather and park factors
echo   🎯 Game mappings and IDs
echo   📋 Enhanced Rotowire lineup confirmations (100% coverage)
echo   🔢 Complete batting orders for all teams
echo.
echo 📁 Data files updated in: data\
echo 📋 FD slate with batting orders: fd_current_slate\fd_slate_today.csv
echo.
echo 🚀 NEXT STEPS:
echo   • Run 2_DFS_MODELS.bat for lineup optimization
echo   • Run 3_PROP_MODELS.bat for betting analysis
echo   • Or run both for complete analysis
echo.
echo 💡 TIP: This data pipeline should be run once daily
echo    to refresh all underlying data sources.
echo ========================================
goto end

:error
echo.
echo ========================================
echo ❌ ERROR in data pipeline!
echo ========================================
echo Check the output above for details.
echo.
echo 💡 Common issues and solutions:
echo   • API rate limits → Wait 5-10 minutes and retry
echo   • Network connectivity → Check internet connection
echo   • Missing input files → Run prerequisite steps
echo   • Website structure changes → Check script logs
echo   • Python environment issues → Verify virtual environment
echo.
echo 🔄 Use error_handler.bat to retry individual steps
echo 📧 Check logs for detailed error information
echo.
set /p retry=Do you want to retry the entire pipeline? (y/n): 
if /i "%retry%"=="y" goto :start
goto :end

:end
pause

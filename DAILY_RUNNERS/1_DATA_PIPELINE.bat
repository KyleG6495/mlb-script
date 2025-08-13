@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
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

echo Step 0.5: Fetching Rotowire Confirmed Lineups...
python fetch_rotowire_lineups.py
if errorlevel 1 (
    echo ⚠️ Rotowire fetch failed - continuing with FD data only
) else (
    echo ✅ Rotowire data fetched successfully
)

echo Step 1.5: Creating Starting Lineups Master File...
python create_starting_lineups.py
if errorlevel 1 (
    echo ❌ Failed to create starting lineups master file
    goto error
) else (
    echo ✅ Starting lineups master file created
)

echo Step 1.6: Creating Pipeline-Ready Starters File...
python create_pipeline_ready_starters.py
if errorlevel 1 (
    echo ❌ Failed to create pipeline-ready starters file
    goto error
) else (
    echo ✅ Pipeline-ready starters file created - data pipeline will use ONLY confirmed starters
)

echo Step 1: Generating Hitter Games (Confirmed Starters Only)...
python "1. generate_hitter_games.py"
if errorlevel 1 goto error

echo Step 2: Assigning Hitter IDs...
python "2. assign_hitter_ids.py"
if errorlevel 1 goto error

echo Step 3: Assigning Hitter Game PKs...
python "3. assign_hitter_game_pk.py"
if errorlevel 1 goto error

echo Step 4: Generating Pitcher Games...
python "4. generate_pitcher_games.py"
if errorlevel 1 goto error

echo Step 5: Assigning Pitcher IDs...
python "5. assign_player_ids.py"
if errorlevel 1 goto error

echo Step 6: Assigning Pitcher Game PKs...
python "6. assign_pitcher_game_pk.py"
if errorlevel 1 goto error

echo Step 7: Scraping Hitter Stats...
python "7. scrape_hitter_stats.py"
if errorlevel 1 goto error

echo Step 8: Scraping Pitcher Stats...
python "8. scrape_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 9: Fetching Earned Runs...
python "9. fetch_earned_runs.py"
if errorlevel 1 goto error

echo Step 10: Aggregating Pitcher Stats...
python "10. aggregate_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 11: Building Today Pitcher Features...
python "11. build_today_pitcher_features.py"
if errorlevel 1 goto error

echo Step 12: Building Rolling Hitter Features...
python "12. build_rolling_hitter_features.py"
if errorlevel 1 goto error

echo Step 13: Building Rolling Pitcher Features...
python "13. build_rolling_pitcher_features.py"
if errorlevel 1 goto error

echo Step 14: Building Today Hitter Features...
python "14. build_today_hitter_features.py"
if errorlevel 1 goto error

echo Step 15: Merging Hitter Features...
python "15. merge_hitter_features.py"
if errorlevel 1 goto error

echo Step 16: Merging Pitcher Features...
python "16. merge_pitcher_features.py"
if errorlevel 1 goto error

echo Step 17: Generating Hitter Team Map...
python "17. generate_hitter_team_map.py"
if errorlevel 1 goto error

echo Step 18: Generating Pitcher Team Map...
python "18. generate_pitcher_team_map.py"
if errorlevel 1 goto error

echo Step 19: Building Weather Data...
python "19. build_weather_today.py"
if errorlevel 1 goto error

echo Step 20: Merging Weather and Park Factors...
python "20. merge_weather_and_park_factors.py"
if errorlevel 1 goto error

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
echo   📋 Rotowire lineup confirmations (when available)
echo.
echo 📁 Data files updated in: data\
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
echo ❌ ERROR in data pipeline!
echo Check the output above for details.
echo.
echo Common issues:
echo   • API rate limits (wait and retry)
echo   • Network connectivity
echo   • Missing input files
echo   • Website structure changes
echo.

:end
pause

@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🎯 CONFIRMED STARTERS DATA PIPELINE
echo   Processing ONLY confirmed starters
echo ========================================
echo.
echo Current directory: %CD%
echo This processes data for confirmed starters only
echo Estimated time: ~8-12 minutes (much faster!)
echo.
echo Prerequisites:
echo   ✅ fd_slate_today.csv updated
echo   ✅ starting_lineups.csv created
echo   ✅ fd_slate_starters_only.csv ready
echo.
echo Press any key to start confirmed starters data processing...
pause
echo.
if errorlevel 1 goto error

echo Step 4: Generating pitcher games (confirmed only)...
python "..\4. generate_pitcher_games.py"
if errorlevel 1 goto error

echo Step 5: Using existing pitcher ID assignment...
python "..\5. assign_player_ids.py"
if errorlevel 1 goto error

echo Step 6: Using existing pitcher game PK assignment...
python "..\6. assign_pitcher_game_pk.py"
if errorlevel 1 goto error

echo Step 7: Scraping hitter stats (your proven scraper)...
python "..\7. scrape_hitter_stats.py"
if errorlevel 1 goto error

echo Step 8: Scraping pitcher stats (your proven scraper)...
python "..\8. scrape_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 9: Fetching earned runs...
python "..\9. fetch_earned_runs.py"
if errorlevel 1 goto error

echo Step 10: Aggregating pitcher stats...
python "..\10. aggregate_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 11: Building today pitcher features...
python "..\11. build_today_pitcher_features.py"
if errorlevel 1 goto error

echo Step 12: Building rolling hitter features...
python "..\12. build_rolling_hitter_features.py"
if errorlevel 1 goto error

echo Step 13: Building rolling pitcher features...
python "..\13. build_rolling_pitcher_features.py"
if errorlevel 1 goto error

echo Step 14: Building today hitter features...
python "..\14. build_today_hitter_features.py"
if errorlevel 1 goto error

echo Step 15: Merging hitter features...
python "..\15. merge_hitter_features.py"
if errorlevel 1 goto error

echo Step 16: Merging pitcher features...
python "..\16. merge_pitcher_features.py"
if errorlevel 1 goto error

echo Step 17: Generating hitter team map...
python "..\17. generate_hitter_team_map.py"
if errorlevel 1 goto error

echo Step 18: Generating pitcher team map...
python "..\18. generate_pitcher_team_map.py"
if errorlevel 1 goto error

echo Step 19: Building weather data...
python "..\19. build_weather_today.py"
if errorlevel 1 goto error

echo Step 20: Merging weather and park factors...
python "..\20. merge_weather_and_park_factors.py"
if errorlevel 1 goto error\Personal_Information\MLB\Scripts"
echo ========================================
echo   🎯 CONFIRMED STARTERS DATA PIPELINE
echo   Processing ONLY confirmed starters
echo ========================================
echo.
echo Current directory: %CD%
echo This processes data for confirmed starters only
echo Estimated time: ~8-12 minutes (much faster!)
echo.

echo Step 0: Ensure confirmed starters slate exists...
if not exist "..\fd_current_slate\fd_slate_confirmed_starters_only.csv" (
    echo ❌ Confirmed starters slate not found!
    echo 💡 Run DAILY_CONFIRMED_WORKFLOW.bat first
    pause
    exit /b 1
)

python -c "
import pandas as pd
confirmed_df = pd.read_csv('../fd_current_slate/fd_slate_confirmed_starters_only.csv')
print(f'✅ Found {len(confirmed_df)} confirmed starters')
print(f'   Pitchers: {len(confirmed_df[confirmed_df[\"Position\"] == \"P\"])}')
print(f'   Hitters: {len(confirmed_df[confirmed_df[\"Position\"] != \"P\"])}')
print(f'   Games: {list(confirmed_df[\"Game\"].unique())}')
"

echo.
echo Press any key to start confirmed starters data processing...
pause
echo.

echo Step 1: Generating Confirmed Hitter Games...
python "1_CONFIRMED_generate_hitter_games.py"
if errorlevel 1 goto error

echo Step 2: Assigning Confirmed Hitter IDs...
python "2_CONFIRMED_assign_hitter_ids.py"
if errorlevel 1 goto error

echo Step 3: Assigning Confirmed Hitter Game PKs...
python "3_CONFIRMED_assign_hitter_game_pk.py"
if errorlevel 1 goto error

echo Step 4: Generating Confirmed Pitcher Games...
python "4_CONFIRMED_generate_pitcher_games.py"
if errorlevel 1 goto error

echo Step 5: Assigning Confirmed Pitcher IDs...
python "5_CONFIRMED_assign_player_ids.py"
if errorlevel 1 goto error

echo Step 6: Assigning Confirmed Pitcher Game PKs...
python "6_CONFIRMED_assign_pitcher_game_pk.py"
if errorlevel 1 goto error

echo Step 7: Scraping Confirmed Hitter Stats...
python "7_CONFIRMED_scrape_hitter_stats.py"
if errorlevel 1 goto error

echo Step 8: Scraping Confirmed Pitcher Stats...
python "8_CONFIRMED_scrape_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 9: Fetching Confirmed Earned Runs...
python "9_CONFIRMED_fetch_earned_runs.py"
if errorlevel 1 goto error

echo Step 10: Aggregating Confirmed Pitcher Stats...
python "10_CONFIRMED_aggregate_pitcher_stats.py"
if errorlevel 1 goto error

echo Step 11: Building Today Confirmed Pitcher Features...
python "11_CONFIRMED_build_today_pitcher_features.py"
if errorlevel 1 goto error

echo Step 12: Building Rolling Confirmed Hitter Features...
python "12_CONFIRMED_build_rolling_hitter_features.py"
if errorlevel 1 goto error

echo Step 13: Building Rolling Confirmed Pitcher Features...
python "13_CONFIRMED_build_rolling_pitcher_features.py"
if errorlevel 1 goto error

echo Step 14: Building Today Confirmed Hitter Features...
python "14_CONFIRMED_build_today_hitter_features.py"
if errorlevel 1 goto error

echo Step 15: Merging Confirmed Hitter Features...
python "15_CONFIRMED_merge_hitter_features.py"
if errorlevel 1 goto error

echo Step 16: Merging Confirmed Pitcher Features...
python "16_CONFIRMED_merge_pitcher_features.py"
if errorlevel 1 goto error

echo Step 17: Generating Confirmed Hitter Team Map...
python "17_CONFIRMED_generate_hitter_team_map.py"
if errorlevel 1 goto error

echo Step 18: Generating Confirmed Pitcher Team Map...
python "18_CONFIRMED_generate_pitcher_team_map.py"
if errorlevel 1 goto error

echo Step 19: Building Weather Data for Confirmed Games...
python "19_CONFIRMED_build_weather_today.py"
if errorlevel 1 goto error

echo Step 20: Merging Weather and Park Factors for Confirmed Games...
python "20_CONFIRMED_merge_weather_and_park_factors.py"
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 CONFIRMED STARTERS PIPELINE COMPLETE!
echo ========================================
echo.
echo ✅ Processed data for confirmed starters only:
echo   📊 Hitter stats and features (confirmed players)
echo   ⚾ Pitcher stats and features (confirmed starters)
echo   🌤️ Weather and park factors (confirmed games)
echo   🎯 Game mappings and IDs (confirmed matchups)
echo.
echo 📁 Confirmed data files updated in: data\
echo.
echo 🚀 ADVANTAGES OF CONFIRMED-ONLY PROCESSING:
echo   ⚡ 3x faster processing (43 vs 283 players)
echo   🎯 100%% focused on players that will actually play
echo   💾 Smaller, more manageable datasets
echo   🚫 Zero waste on bench/non-starting players
echo.
echo 🎯 NEXT STEPS:
echo   • Run confirmed starters projection models
echo   • Run confirmed starters lineup optimization
echo   • Submit disaster-proof lineups!
echo.
echo 💡 TIP: This runs on confirmed starters only
echo    Much faster and more accurate than full league!
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in confirmed starters pipeline!
echo Check the output above for details.
echo.
echo Common issues:
echo   • Missing confirmed starters slate
echo   • Player name matching issues
echo   • API rate limits (less likely with fewer players)
echo   • Network connectivity
echo.
echo 💡 SOLUTION: Ensure DAILY_CONFIRMED_WORKFLOW.bat ran successfully first
echo.

:end
pause

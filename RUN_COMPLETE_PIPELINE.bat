@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   MLB AUTOMATED BETTING SYSTEM
echo   COMPLETE DAILY PIPELINE
echo ========================================
echo.
echo Current directory: %CD%
echo This will run all 24 steps + ML analysis
echo Total time: ~45-60 minutes
echo.
echo Press any key to start, or Ctrl+C to cancel...
pause
echo.

echo Step 1: Generating Hitter Games...
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

echo Step 21: Finalizing Hitter Features...
python "(21)finalize_hitter_features.py"
if errorlevel 1 goto error

echo Step 22: Finalizing Pitcher Features...
python "(22)finalize_pitcher_features.py"
if errorlevel 1 goto error

echo Step 23: Adding Pitcher Context...
python add_pitcher_features.py
if errorlevel 1 goto error

echo Step 24: Applying Real Player Stats...
python fix_prediction_features_with_real_stats.py
if errorlevel 1 goto error

echo Step 25: Running ML Analysis...
python automated_betting_system.py
if errorlevel 1 goto error

echo Step 26: Running Enhanced FanDuel Optimizer...
python enhanced_fanduel_optimizer.py
if errorlevel 1 goto error

echo Step 26b: Running Standard FanDuel Optimizer (for comparison)...
python "23. optimize_fanduel_lineup.py"
if errorlevel 1 goto error

echo Step 27: Creating FanDuel Submission...
python "24. create_fanduel_submission.py"
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 COMPLETE PIPELINE FINISHED! 
echo.
echo Check the following folders for results:
echo   Betting Analysis: betting_analysis\
echo   FanDuel Enhanced Lineups: data\ (enhanced_lineup_*.csv)
echo   FanDuel Standard Lineup: data\ (optimized_lineup.csv)
echo.
echo Files created:
echo   📋 betting_report_*.txt (betting summary)
echo   📊 betting_opportunities_*.csv (betting detailed)
echo   🔥 enhanced_lineup_*.csv (ENHANCED FanDuel lineups - USE THESE!)
echo   🏆 optimized_lineup.csv (standard FanDuel lineup)
echo   📝 fanduel_submission_names.csv (submission file)
echo.
echo To start live monitoring, run:
echo   python live_betting_runner.py
echo ========================================
goto end

:error
echo.
echo ❌ ERROR occurred in pipeline!
echo Check the output above for details.
echo.

:end
pause

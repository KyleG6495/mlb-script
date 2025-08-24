@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🏆 DFS & FANTASY LINEUP OPTIMIZATION
echo   Model-Based Lineup Generation
echo ========================================
echo.
echo Current directory: %CD%
echo This runs ML models to optimize FanDuel lineups
echo Total time: ~8-12 minutes
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (RUN_DATA_PIPELINE.bat)
echo   ✅ fd_slate_today.csv updated with today's slate
echo.
echo Press any key to start lineup optimization...
pause
echo.

echo Step 1: Finalizing Hitter Features...
python "(21)finalize_hitter_features.py"
if errorlevel 1 goto error

echo Step 2: Finalizing Pitcher Features...
python "(22)finalize_pitcher_features.py"
if errorlevel 1 goto error

echo Step 3: Adding Pitcher Context...
python add_pitcher_features.py
if errorlevel 1 goto error

echo Step 4: Applying Real Player Stats...
python fix_prediction_features_with_real_stats.py
if errorlevel 1 goto error

echo Step 5: Running Unified DFS Optimization...
python UNIFIED_DFS_SYSTEM.py
if errorlevel 1 goto error

echo Step 6: Creating Additional Lineup Formats...
python "24. create_fanduel_submission.py"
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 DFS OPTIMIZATION COMPLETE! 
echo ========================================
echo.
echo 🎯 LINEUP FILES CREATED:
echo   📊 unified_dfs_lineups_*.csv (detailed 20 lineups)
echo   📋 unified_dfs_summary_*.csv (lineup overview)
echo   🎯 fanduel_submission_*.csv (ready to upload)
echo   📝 fanduel_submission_names.csv (alternate format)
echo.
echo 🏆 LINEUP BREAKDOWN:
echo   • 3 FLOOR lineups (cash games, high floor)
echo   • 14 BALANCED lineups (all-purpose optimal)
echo   • 3 CEILING lineups (tournaments, high upside)
echo.
echo 💰 VALIDATION CHECKS:
echo   ✅ $35,000 salary cap enforced
echo   ✅ 9 players per lineup (P+C+1B+2B+3B+SS+3OF)
echo   ✅ Enhanced projections with weather/matchups
echo   ✅ Lineup diversity (no duplicates)
echo.
echo 🚀 READY FOR FANDUEL SUBMISSION!
echo   Upload: fanduel_submission_*.csv
echo.
echo 💡 STRATEGY GUIDE:
echo   • Cash games → Use FLOOR lineups
echo   • GPP tournaments → Use CEILING lineups  
echo   • Mixed contests → Use BALANCED lineups
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in DFS optimization!
echo Check the output above for details.
echo.
echo Troubleshooting checklist:
echo   ❓ Did you run RUN_DATA_PIPELINE.bat first?
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

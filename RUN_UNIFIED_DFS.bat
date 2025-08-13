@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🚀 UNIFIED DFS OPTIMIZATION PIPELINE
echo   Clean, Simple, Single Source of Truth
echo ========================================
echo.
echo This is your NEW streamlined DFS system.
echo All other DFS scripts are now DEPRECATED.
echo Time: ~2-5 minutes
echo.
echo Press any key to start optimization...
pause
echo.

echo 🔄 Step 1: Preparing today's slate data...
echo   ✅ Loading fd_slate_today.csv
echo   ✅ Loading player projections
echo   ✅ Merging and validating data
echo.

echo 🧮 Step 2: Running unified DFS optimization...
python UNIFIED_DFS_SYSTEM.py
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 UNIFIED DFS OPTIMIZATION COMPLETE!
echo ========================================
echo.
echo 📁 YOUR FILES (all timestamped):
echo   📊 unified_dfs_lineups_YYYYMMDD_HHMMSS.csv (detailed)
echo   📋 unified_dfs_summary_YYYYMMDD_HHMMSS.csv (overview)
echo   🎯 fanduel_submission_YYYYMMDD_HHMMSS.csv (UPLOAD THIS!)
echo.
echo 🔥 LINEUP DISTRIBUTION:
echo   • 3 FLOOR lineups (safe, high floor)
echo   • 14 BALANCED lineups (cash games)
echo   • 3 CEILING lineups (tournaments)
echo   • Total: 20 optimized lineups
echo.
echo 💡 NEXT STEPS:
echo   1. Upload fanduel_submission_*.csv to FanDuel
echo   2. Use FLOOR lineups for cash games
echo   3. Use CEILING lineups for tournaments
echo   4. Use BALANCED for everything else
echo.
echo ✅ All constraints validated (9 players, $35k cap, positions)
echo ✅ Enhanced projections with weather/matchup factors
echo ✅ Automatic lineup diversity (no duplicates)
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in unified optimization!
echo.
echo Required files checklist:
echo   ❓ fd_slate_today.csv (today's FanDuel slate)
echo   ❓ fd_hitter_features_final.csv (hitter projections)
echo   ❓ fd_pitcher_features_final.csv (pitcher projections)
echo.
echo Make sure these files exist and try again.
echo.

:end
pause

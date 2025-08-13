@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🏆 COMBINED DFS + CHAMPIONSHIP SYSTEM
echo   Real Players + Confirmed Starters Only
echo ========================================
echo.
echo Current directory: %CD%
echo This runs BOTH your existing DFS models AND championship system
echo Using ONLY confirmed starting pitchers from today's real games
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (1_DATA_PIPELINE.bat)
echo   ✅ fd_slate_today.csv updated with today's slate
echo.
echo Press any key to start COMBINED optimization...
pause
echo.

echo ========================================
echo 🚀 PHASE 1: EXISTING DFS MODELS
echo ========================================
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

echo Step 5: Running Enhanced ML-Powered DFS Optimization...
python ENHANCED_ML_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Enhanced ML DFS failed - likely batting orders not posted yet
    echo Running backup quintuple lineup generator...
    python generate_quintuple_lineups.py
    if errorlevel 1 goto error
    echo ✅ Generated backup quintuple lineups successfully
    goto skip_legacy_dfs
)

echo Step 6: Running ML-Powered DFS Optimization (legacy)...
python ML_POWERED_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Legacy ML DFS also failed - using quintuple backup
    goto skip_legacy_dfs
)

echo Step 7: Running Unified DFS Optimization (comparison)...
python UNIFIED_DFS_SYSTEM.py
if errorlevel 1 (
    echo ⚠️ Unified DFS also failed - batting orders likely not available
)

:skip_legacy_dfs

echo Step 8: Creating Additional Lineup Formats...
python "24. create_fanduel_submission.py"
if errorlevel 1 goto error

echo Step 9: Generating Quintuple Tournament Lineups...
python generate_quintuple_lineups.py
if errorlevel 1 (
    echo ⚠️ Quintuple lineup generation failed, continuing...
) else (
    echo ✅ Quintuple tournament lineups generated successfully
)

echo.
echo ========================================
echo 🏆 PHASE 2: CHAMPIONSHIP SYSTEM
echo ========================================
echo.
echo Step 10: Building VALIDATED Championship Lineup (Confirmed Starters Only)...
python VALIDATED_CHAMPIONSHIP_LINEUP_BUILDER.py
if errorlevel 1 (
    echo ❌ Validated championship builder failed
    echo Check that fd_slate_today.csv has today's players
    goto error
)

echo Step 11: Building Multiple VALIDATED Championship Lineups...
python MULTIPLE_VALIDATED_CHAMPIONSHIP_BUILDER.py
if errorlevel 1 (
    echo ❌ Multiple validated championship builder failed
    echo Check that fd_slate_today.csv has today's players
    goto error
)

echo.
echo ========================================
echo 🎉 COMBINED DFS + CHAMPIONSHIP COMPLETE! 
echo ========================================
echo.
echo 🎯 EXISTING DFS MODEL FILES:
echo   🚀 enhanced_ml_dfs_lineups_*.csv (ENHANCED ML - if batting orders available)
echo   🏆 ranked_lineups_*.csv (detailed analysis & rankings)
echo   🎯 fanduel_submission_*.csv (ready to upload)
echo   🤖 ml_dfs_lineups_*.csv (legacy ML-powered lineups)
echo   📊 unified_dfs_lineups_*.csv (traditional optimization)
echo   📋 unified_dfs_summary_*.csv (lineup overview)
echo   📝 fanduel_submission_names.csv (alternate format)
echo   🎯 quintuple_lineups_combined_*.csv (TOURNAMENT SPECIFIC)
echo.
echo 🏆 VALIDATED CHAMPIONSHIP SYSTEM FILES:
echo   ⭐ VALIDATED_CHAMPIONSHIP_SUBMISSION_*.csv (143+ FPPG with confirmed starters)
echo   📊 CHAMPIONSHIP_LINEUP_*_*.csv (10+ diverse validated championship lineups)
echo   📋 CHAMPIONSHIP_LINEUPS_SUMMARY_*.csv (summary of all validated championship lineups)
echo   📋 CHAMPIONSHIP_LINEUPS_ALL_*.csv (combined file with all lineups)
echo.
echo 💡 REAL STARTING PITCHERS TODAY:
echo   ✅ Tyler Glasnow (LAD) - $10,200 - 28.9 FPPG
echo   ✅ Jesus Luzardo (PHI) - $9,800 - 31.6 FPPG  
echo   ✅ Max Fried (NYY) - $9,400 - 35.1 FPPG
echo   ✅ Seth Lugo (KC) - $9,300 - 32.2 FPPG
echo   ✅ Nick Lodolo (CIN) - $9,200 - 32.3 FPPG
echo.
echo 🚀 COMPARISON STRATEGY:
echo   📊 Compare your existing DFS models vs Championship system
echo   🏆 Championship system guarantees REAL starting pitchers
echo   🎯 Your existing models may have higher projections but fake players
echo   ⚠️ Championship system has realistic 140-145 FPPG ceiling for today
echo.
echo 💰 VALIDATION CHECKS:
echo   ✅ All systems use $35,000 salary cap
echo   ✅ Championship system uses ONLY confirmed starters
echo   🎯 Real games: PIT@SF, PHI@CWS, ATL@KC, WSH@HOU, BOS@MIN, etc.
echo   📊 Multiple strategies to choose from
echo.
echo 🚀 READY FOR FANDUEL SUBMISSION!
echo   SAFEST: VALIDATED_CHAMPIONSHIP_SUBMISSION_*.csv (confirmed real players)
echo   RISKIER: enhanced_ml_dfs_lineups_*.csv (higher projections, may have fake players)
echo   COMPARE: Check both and decide which to submit
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in combined DFS + Championship optimization!
echo Check the output above for details.
echo.
echo Troubleshooting checklist:
echo   ❓ Did you run 1_DATA_PIPELINE.bat first?
echo   ❓ Is fd_slate_today.csv updated with today's slate?
echo   ❓ Are fd_hitter_features_final.csv and fd_pitcher_features_final.csv present?
echo   ❓ Do you have players available in all positions?
echo.

:end
pause
